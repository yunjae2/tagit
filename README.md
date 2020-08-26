# tagit

`tagit` is a command-line tagging system for experimental data, focusing on getting rid of
researchers' waste of time on arranging / manipulating / moving the experimental data.

### Core functionality
* Record shell command output with tags.
* Report data with specified tags in various format (terminal, csv file, and hierarchical files).
* List tags.
* Import/export data dump between systems.


### Directory
- [Basic concepts](#basic-concepts)
- [Tutorial](#tutorial)
- [Usage](#usage)
  - [Main commands](#main-commands)
  - [Other commands](#other-commands)
  
  
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


## Basic concepts
`tagit` has three main concepts: experiments, tags, and data.
* An _experiment_ is a set of tagged data.
Data in the same experiment commonly share a number of tags with different values.
The name came from scientific methods,
which usually involves collection of experiment results with different set of variables (which corresponds to tags in `tagit`).
* A _tag_ is similar to variable in scientific experiments;
it has a key and multiple values (e.g., "color=red", "color=yellow").
Since it is quite common for tags to stick to the _optimal_ or _final_ value in experiments, 
A tag may have the default value (coming soon!)
* A _data_ is the element of `tagit`.
Each data may have multiple tags (e.g., "color=red, shape=sphere").


## Tutorial
```
# 1. Record the data
$ tagit record figures "color=red, shape=sphere, weight=10kg" -- echo "A red ball"
A red ball

$ tagit record figures "color=green, shape=sphere, weight=5kg" -- echo "A green ball"
A green ball

$ tagit record figures "color=yellow, shape=cube, weight=10kg" -- echo "A yellow box"
A yellow box


# 2. List experiments
$ tagit list
figures


# 3. Report the data
$ tagit report figures
[figures] (color=red, shape=sphere, weight=10kg)
A red ball
[figures] (color=green, shape=sphere, weight=5kg)
A green ball
[figures] (color=yellow, shape=cube, weight=10kg)
A yellow box

$ tagit report tutorial "shape=sphere, weight, color"
[figures] (shape=sphere, weight=10kg, color=red)
A red ball
[figures] (shape=sphere, weight=5kg, color=green)
A green ball


# 4. Delete a data
$ tagit manage figures -r "weight=10kg"

$ tagit report figures
[figures] (color=green, shape=sphere, weight=5kg)
A green ball


# 5. Delete an experiment
$ tagit manage figures -d

$ tagit list

```


## Usage
### Main commands
#### 1. `record`
```
$ tagit record <exp_name> <tags> -- <command>
```
Records the output of `<command>` tagged with `<tags>` in `<exp_name>` space.
`<tags>` must be specified with double quotes (e.g., `$ tagit record myexp "a=1, b=2", -- ./run_exp.sh`)


#### 2. `report`
```
$ tagit report [-c <csv_file>] [-f <path>] <exp_name> [<tags>]
```
Reports the data in `<exp_name>` space.
If <tags> are specified, tagit reports data corresponding to the specified tags.
By default, the result is printed in terminal.

* Tag order
  - Users can specify the tag order in `<tag>`. For example, `"c=3, b=2, a=1"` makes tags printed in c-b-a order.
  - Also, tag can be specified without values like `"c, b=2, a"`.
  This is for setting the tag order without changing the report scope.

* Result format options
  - `-c`: Print the result in csv format
  - `-f`: Print the result in file hierarchy; each data is saved as a file under the nested directory path, where each directory corresponds to a tag


#### 3. `manage`
```
$ tagit manage [-d] [-r [<tags>]] <exp_name>
```
Manages recorded data in <exp_name> space.

* Manange options
  - `-d`: Delete an experiment.
  - `-r`: Delete data corresponding to the specified tags in an experiment.
  This does not delete an experiment, even though every data is deleted.

### Other commands
#### 1. `list`
```
$ tagit list [<exp_name>]
```
List the experiments. If `<exp_name>` is specified, it lists the name of tags in the specified experiment instead.


#### 2. `export`
```
$ tagit export <output_dump>
```
Export all experiment and data to `<output_dump>` in the format of sql script.


#### 3. `import`
```
$ tagit import <db_dump>
```
Import experiments and data from `<db_dump>`. `<db_dump>` must be a sql script.


## Notes
This tools is currently alpha version and may contain lots of bugs.
Issues / pull requests about new features, bug reports are appreciated.
