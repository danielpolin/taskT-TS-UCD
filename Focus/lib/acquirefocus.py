import os
import time
import fp
from org.lsst.ccs.utilities.location import LocationSet
import ucd_bench
import ucd_stage
import logging
import JFitsUtils

logger = logging.getLogger(__name__)

TEST_SEQ_NUM = 0

class TestCoordinator(object):
    """Base class for taking images.

    Parameters
    ----------
    options : `dict`
       Dictionary contining image acquisition options.
    test_type : `str`
       Type of acquisition test.
    image_type : `str`
       Type of image.
    """

    def __init__(self, options, test_type, image_type):
        self.run = options['run']
        self.test_type = test_type
        self.image_type = image_type
        self.annotation = options.get('annotation', '')
        self.locations = LocationSet(options.get('locations', ''))
        self.clears = options.getInt('clears', 1)
        self.extra_delay = options.getFloat('extradelay', 0)
        self.description = options.get('description', None)
        self.delete = options.getInt('delete', 1)

        logger.info("{0} Test Description: {1}".format(self.test_type, self.description))

    def take_images(self):
        raise NotImplementedError

    def take_bias_images(self, count):
        """Take multiple bias images.

        Parameters
        ----------
        count : `int`
            Number of bias images to take.
        """
        for i in range(count):
            self.take_bias_image()

    def create_fits_header_data(self, exposure, image_type):
        """Create a dictionary of FITS header keyword names and values.

        Parameters
        ----------
        exposure : `float`
            Exposure time in seconds.
        image_type : `str`
            Description of the image type.

        Returns
        -------
        data : `dict`
            Dictionary of FITS header keyword names and values.
        """
        data = {'ExposureTime' : exposure, 
                'TestType' : self.test_type,
                'ImageType' : image_type}

        if self.run:
            data.update({'RunNumber' : self.run})

        return data

    def take_bias_image(self):
        """Take a bias image."""
        return self.__take_image(0, None, image_type='BIAS')

    def take_image(self, exposure, expose_command, image_type=None):
        """Take a test image."""
        return self.__take_image(exposure, expose_command, image_type)

    def __take_image(self, exposure, expose_command, image_type=None):
        """Base method for taking an image.

        Parameters
        ----------
        exposure : `float`
            Exposure time in seconds.
        expose_command : `function`
            A callable that defines the exposure.
        image_type : `str`
            Description of the image type.
        """
        global TEST_SEQ_NUM

        image_type = image_type if image_type else self.image_type

        ## Wait for optional extra delay before image
        if self.extra_delay > 0:
            logger.info("Extra delay %g" % self.extra_delay)
            time.sleep(self.extra_delay)

        fits_header_data = self.create_fits_header_data(exposure, image_type)
        file_info = fp.takeExposure(expose_command, fits_header_data, self.annotation, self.locations, 
                                    self.clears)

        ## Perform image file management
        for f in file_info:

            filepath = f.toString()

            ## Remove flush bias or reorder amplifiers
            if filepath.endswith('S01.fits'):
                if TEST_SEQ_NUM < self.delete and image_type == 'BIAS':
                    os.remove(filepath)
                    logger.debug("{0} removed.".format(filepath))
                    logger.info("Flush bias removed: {0}".format(filepath))
#                else:
#                    JFitsUtils.reorder_hdus(filepath)
#                    logger.debug("{0} amplifiers reordered.".format(filepath))
#                    logger.info("Image Type: {0}, File Path: {1}".format(image_type, filepath))

            ## Remove unused images
            elif filepath.endswith('S00.fits') or filepath.endswith('S02.fits'):
                os.remove(filepath)
                logger.debug("{0} removed.".format(filepath))

        TEST_SEQ_NUM += 1

        return file_info

class BiasTestCoordinator(TestCoordinator):
    """A TestCoordinator for taking only bias images."""

    def __init__(self, options):
        super(BiasTestCoordinator, self).__init__(options, 'BIAS', 'BIAS')
        self.count = options.getInt('count', 10)
        ucd_bench.turnLightOff()
        logger.info("Bias Images: {0}".format(self.count))

    def take_images(self):
        """Take multiple bias images."""
        self.take_bias_images(self.count)

class BiasPlusImagesTestCoordinator(TestCoordinator):
    """Base Class for all tests that involve n bias images per test image."""

    def __init__(self, options, test_type, image_type):
        super(BiasPlusImagesTestCoordinator, self).__init__(options, test_type, image_type)
        self.bcount = int(options.get('bcount', '1'))
        self.intensity = 30.0
        self.current = 0.0

    def take_bias_plus_image(self, exposure, expose_command, image_type=None):
        """Take a bias image and a test image."""
        self.take_bias_images(self.bcount)
        self.take_image(exposure, expose_command, image_type)

class DarkTestCoordinator(BiasPlusImagesTestCoordinator):
    """A TestCoordinator for darks."""

    def __init__(self, options):
        super(DarkTestCoordinator, self).__init__(options, 'DARK', 'DARK')
        self.darks = options.getList('dark')
        ucd_bench.turnLightOff()
        logger.info("Biases per Dark: {0}".format(self.bcount))

    def take_images(self):
        """Take multiple dark images."""
        for dark in self.darks:
            integration, count = dark.split()
            integration = float(integration)
            count = int(count)
            logger.info("Darks: {0}, Integration Time {1:.1f} sec".format(count, integration))
            expose_command = lambda: time.sleep(integration)

            for c in range(count):
                self.take_bias_plus_image(integration, expose_command)

class FlatFieldTestCoordinator(BiasPlusImagesTestCoordinator):
    """A TestCoordinator for flats."""

    def __init__(self, options):
        super(FlatFieldTestCoordinator, self).__init__(options, 'FLAT', 'FLAT')
        self.flats = options.getList('flat')
        self.wl_filter = options.get('wl')
        ucd_bench.turnLightOn()

        logger.info("Biases per Flat: {0}".format(self.bcount))

    def take_images(self):
        """Take multiple flat field images."""
        for flat in self.flats:
    
            ## Get flat parameters
            exposure, intensity, count = flat.split()
            exposure = float(exposure)
            intensity = float(intensity)
            count = int(count)

            if self.intensity != intensity:
                ucd_bench.setLightIntensity(intensity)
                self.intensity = intensity
                self.current = ucd_bench.readPhotodiodeCurrent()

            logger.info("Flats: {0}, Exposure Time: {1}".format(count, exposure))
            logger.debug("Photodiode: {0}".format(self.current))

            ## Perform acquisition
            expose_command = lambda : ucd_bench.openShutter(exposure)
            for c in range(count):
                self.take_bias_plus_image(exposure, expose_command)

    def create_fits_header_data(self, exposure, image_type):
        data = super(FlatFieldTestCoordinator, self).create_fits_header_data(exposure, image_type)
        if image_type != 'BIAS':
            data.update({'FilterName' : self.wl_filter,
                         'PdCurrent' : self.current})
        return data

class PersistenceTestCoordinator(BiasPlusImagesTestCoordinator):
    """A TestCoordinator for persistence images."""
    def __init__(self, options):
        super(PersistenceTestCoordinator, self).__init__(options, "PERSISTENCE", "SPOT")
        self.bcount = options.getInt('bcount', 10)
        self.persistence = options.getList('persistence')
        self.mask = options.get('mask')
        ucd_bench.turnLightOn()

        logger.info("Biases per Persistence Image: {0}".format(self.bcount))

    def take_images(self):

        ## Get persistence parameters
        exposure, intensity, n_of_dark, exp_of_dark, t_btw_darks= self.persistence[0].split()
        exposure = float(exposure)
        intensity = float(intensity)

        if self.intensity != intensity:
            ucd_bench.setLightIntensity(intensity)
            self.intensity = intensity
            self.current = ucd_bench.readPhotodiodeCurrent()

        ## Bias acquisitions
        self.take_bias_images(self.bcount)

        ## Flat acquisition
        logger.info("Persistence Image Exposure Time: {0}".format(exposure)) 
        expose_command = lambda: ucd_bench.openShutter(exposure)
        file_list = super(PersistenceTestCoordinator, self).take_image(exposure, expose_command, "SPOT")

        ## Dark acquisition
        exp_of_dark = float(exp_of_dark)
        n_of_dark = int(n_of_dark)
        t_btw_darks = float(t_btw_darks)
        logger.info("Darks: {0}, Integration Time: {1} sec, Time Between Darks: {2} sec".format(n_of_dark, 
                                                                                                exp_of_dark, 
                                                                                                t_btw_darks))
        for i in range(n_of_dark):
            time.sleep(t_btw_darks)
            super(PersistenceTestCoordinator, self).take_image(exp_of_dark, lambda: time.sleep(exp_of_dark), 
                                                               image_type="DARK")

class SpotTestCoordinator(BiasPlusImagesTestCoordinator):
    """A TestCoordinator for spot/streak images."""

    def __init__(self, options):
        super(SpotTestCoordinator, self).__init__(options, 'SPOT', 'SPOT')
        self.imcount = int(options.get('imcount', '1'))
        self.mask = options.get('mask')
        self.exposures = options.getList('expose')
        self.points = options.getList('point')
#        ucd_bench.turnLightOn()
        self.get_current_position()

        logger.info("Mask: {0}, Image Count: {1}, Bias Count: {2}".format(self.mask, self.imcount, self.bcount))

    def get_current_position(self):
        with open('/home/ccd/ucd-scripts/python-lib/StagePosition.py', 'r') as f:
            lines = f.readlines()
            x, y, z = lines[0].split("=")[1][1:-1].split(",")
        self.stagex = int(x)
        self.stagey = int(y)
        self.stagez = int(z)

    def take_images(self):
        """Take multiple spot images."""
        def moveTo(point):
            """A wrapper to 'moveTo' to store the current position."""
            splittedpoints = point.split()
            x = int(float(splittedpoints[0]))
            y = int(float(splittedpoints[1]))
            z = int(float(splittedpoints[2]))
            if self.stagex == x and self.stagey == y and self.stagez == z:
                return
            else:
                ucd_stage.moveTo(x, y, z)
                self.get_current_position()

        for point in self.points:
            moveTo(point)

            for item in self.exposures:
                
                exposure, intensity = item.split()
                exposure = float(exposure)
                intensity = float(intensity)

                if self.intensity != intensity:
                    ucd_bench.setLightIntensity(intensity)
                    self.intensity = intensity
                    self.current = ucd_bench.readPhotodiodeCurrent()

                expose_command = lambda: ucd_bench.openShutter(exposure)
                for i in range(self.imcount):
                    self.take_bias_plus_image(exposure, expose_command)

    def create_fits_header_data(self, exposure, image_type):
        data = super(SpotTestCoordinator, self).create_fits_header_data(exposure, image_type)
        if image_type != 'BIAS':
            data.update({'StageX' : self.stagex,
                         'StageY' : self.stagey,
                         'StageZ' : self.stagez,
                         'PdCurrent' : self.current})
        return data

def do_bias(options):
    """Initialize a BiasTestCoordinator and take images."""
    tc = BiasTestCoordinator(options)
    tc.take_images()

def do_dark(options):
    """Initialize a DarkTestCoodrinator and take images."""
    tc = DarkTestCoordinator(options)
    tc.take_images()

def do_flat(options):
    """Initialize a FlatFieldTestCoordinator and take images."""
    tc = FlatFieldTestCoordinator(options)
    tc.take_images()
   
def do_persistence(options):
    """Initialize a PersistenceTestCoordinator and take images."""
    tc = PersistenceTestCoordinator(options)
    tc.take_images()

def do_spot(options):
    """Initialize a SpotTestCoordinator and take images."""
    logger.info("spot called {0}".format(options))
    tc = SpotTestCoordinator(options)
    tc.take_images()    
