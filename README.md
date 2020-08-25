# tagit

`tagit` is a command-line tagging system for experiment data, focusing on getting rid of
researchers' waste of time on arranging the experiment data.


## An example: Lisa's story
Consider a curious sysadmin intern, Lisa, trying to discover the effect of system configurations on the performance (i.e. throughput) of server workloads.
Lisa measures the performance by changing system configurations: OS, memory size, storage device, network, database and the number of worker threads.
Since the total number of configuration sets is large (6 configurations with 3 different values each result in 729 combinations!),
Lisa writes a simple script to record the experiment result hierarchically;
configuration values are saved as directory trees (e.g., `ubuntu1804/8/HDD/10/mysql/16/result.txt`).
After all combinations are tested, Lisa wants to analyze the results using spreadsheet, however,
only the raw data is saved under directory structure.
Lisa googles out and notices that she should do the two jobs:
convert each data to useful data, and accumulate them into one file (e.g., .csv) that spreadsheet apps can import.
Lisa spends a day to learn utilities needed for extracting like `sed`, `awk` and `grep`,
and she finally makes it to import the data to spreadsheet.

After a month, Lisa decides to present her experiment as it is the last week of the internship.
Unfortunately, she has lost the spreadsheet and what she got is only the raw data itself,
but now Lisa has no problem in using various utilities.
However, Lisa now finds a serious problem: what does '8' mean in the directory path? 
