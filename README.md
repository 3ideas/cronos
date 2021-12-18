
# Cronos
> A set of utilities to logs with time data in it and convert to trace event file format for 



A very nice viewer for the trace event file can be found here https://ui.perfetto.dev/

![Example screenshot](assets/Screenshot1.png)


Format for the time event file can be found here https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview


## Install

The scipt can be found in cronos/convert_time_log.py  it shouldn't have dependencies outside the standard python libraries.


## How to use

Examples of use,

This will generate a trace event file with the name `logs/ADMSClientTiming_07_12_2021.json`
```
python cronos/convert_time_log.py -f logs/ADMSClientTiming_07_12_2021.log
```

To name the output file,
```
python cronos/convert_time_log.py -f logs/ADMSClientTiming_07_12_2021.log -o example.json
```

And to output to stdout
```
python cronos/convert_time_log.py -f logs/ADMSClientTiming_07_12_2021.log -s 
```

Then open and load the generated file into the viewer at https://ui.perfetto.dev/

# Developing

The script has been developed with nbdev as the markup/test env. See https://nbdev.fast.ai/tutorial.html for more information.

