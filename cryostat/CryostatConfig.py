# Configuration file for automated cryostat 
# Daniel Polin 20230420

###############################################################################
# These parameters control the automatic Dewar Fill

Cryostat_is_Cold	= 1		# 1 = Autofill enabled; 0 = autofill disabled
Temp_to_Fill		= -193.8 	# This is the temp to trigger a fill
Min_Fill_Time		= 90.0          # This is the minimum fill time
Fill_Time_Limit 	= 300.0 	# This is the maximum fill time
Overflow_Temp_Limit	= -10.0         # This is the temp on the overflow monitor that stops the fill
