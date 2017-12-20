import sys
import pandas as pd
import os
from matplotlib import pyplot as plt
if len(sys.argv)==2:
	if os.path.isfile(sys.argv[1]):
		f = sys.argv[1]
	else:
		raise IOERROR("No file found")
	df = pd.read_csv(f)
	df.set_index('date_time',inplace=True)
	df.plot()
	plt.show()

else:
	print("Please provide csv")
	sys.exit()
