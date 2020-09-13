# tagit

`tagit` is a command-line tagging system for experimental data, focusing on getting rid of
researchers' waste of time on arranging / manipulating / moving the experimental data.

### Core functionality
* Record shell command output with tags.
* Report data with specified tags in various format (terminal, csv file, and hierarchical files).
* Parse recorded data automatically.
* List tags.
* Import/export data dump between systems.


### Directory
- [Installation](#installation)
- [Basic concepts](#basic-concepts)
- [Tutorial](#tutorial)
- [Usage](#usage)
  - [Main commands](#main-commands)
  - [Other commands](#other-commands)
  

## Installation
`tagit` is distributed via PyPI with the name of `etagit`.
The name of the script is the same as `tagit`, though.
```
$ pip3 install etagit
```


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
`tagit` has five main concepts: experiments, tags, data, data categories, and parsing rules.
* An _experiment_ is a set of tagged data.
Data in the same experiment commonly share a number of tags with different values.
The name came from scientific methods,
which usually involves collection of experiment results with different set of variables (which corresponds to tags in `tagit`).
* A _tag_ is similar to variable in scientific experiments;
it has a key and multiple values (e.g., "color=red", "color=yellow").
Since it is quite common for tags to stick to the _optimal_ or _final_ value in experiments, 
A tag may have the default value (coming soon!)
* A _data_ is the element of `tagit`.
Each data belongs to a data category, and may have multiple tags (e.g., "color=red, shape=sphere").
* A _data category_ describes the characteristic of the recorded data.
It is similar to tag; however, it is used for parsing recorded data.
When data is recorded, its category is `raw` by default,
and the data can be parsed and saved into different categories (e.g., `throughput`, `latency`).
Experimental results or stats are generally recorded in a single place (a simple example is `/proc/vmstat`, which shows the stats of virtual memory subsystem),
thus data categories can be useful for parsing necessary information from the whole data.
* A _parsing rule_ is applied to each recorded data in an experiment to parse it and generate useful data.
The generated data is saved into the data category specified in the parsing rule.
Once a parsing rule is registered in an experiment, it is automatically applied to data recorded in the future, as well as the data already recorded.


## Tutorial
```bash
# 1. Record the data
$ tagit record perf "storage=sata_ssd, mem=16GB" -- ./run_exp.sh
IOPS is 20K
latency is 100u
New experiment: [perf]
[perf] New tag added:
- storage
- mem

$ tagit record perf "storage=nvme_ssd, mem=16GB" -- ./run_exp.sh
IOPS is 40K
latency is 10us 

$ tagit record perf "storage=nvme_ssd, mem=32GB" -- ./run_exp.sh
IOPS is 60K
latency is 10us 



# 2. List experiments
$ tagit list
perf


# 3. Report the data
$ tagit report perf
[perf] (storage=sata_ssd, mem=16GB)
- raw: IOPS is 20K
latency is 100us
[perf] (storage=nvme_ssd, mem=16GB)
- raw: IOPS is 40K
latency is 10us
[perf] (storage=nvme_ssd, mem=32GB)
- raw: IOPS is 60K
latency is 10us

$ tagit report tutorial "mem=16GB, storage"
[figures] (shape=sphere, weight=10kg, color=red)
[perf] (mem=16GB, storage=sata_ssd)
- raw: IOPS is 20K
latency is 100us
[perf] (mem=16GB, storage=nvme_ssd)
- raw: IOPS is 40K
latency is 10us


# 4. Parse recorded data
$ tagit parse add perf iops "awk '/^IOPS/{print \$NF}'"
[perf] New data category:
- iops

$ tagit parse add perf latency "awk '/^latency/{print \$NF}'"
[perf] New data category:
- latency

$ tagit parse list perf
  id  rule                         src    dest     updated
----  ---------------------------  -----  -------  ---------
   0  awk '/^IOPS/{print $NF}'     raw    iops     True
   1  awk '/^latency/{print $NF}'  raw    latency  True

$ tagit report perf -d "latency, iops"
[perf] (storage=sata_ssd, mem=16GB)
- latency: 100us
- iops: 20K
[perf] (storage=nvme_ssd, mem=16GB)
- latency: 10us
- iops: 40K
[perf] (storage=nvme_ssd, mem=32GB)
- latency: 10us
- iops: 60K


# 5. Delete a data
$ tagit manage perf -r "mem=32GB"

$ tagit report perf -d "latency, iops"
[perf] (storage=sata_ssd, mem=16GB)
- latency: 100us
- iops: 20K
[perf] (storage=nvme_ssd, mem=16GB)
- latency: 10us
- iops: 40K


# 6. Delete an experiment
$ tagit manage perf -d

$ tagit list

```


## Usage
### Main commands
#### 1. `record`
```
$ tagit record <exp_name> <tags> [-s <stream>] [-d <data_category>] -- <command>
```
Records the output of `<command>` tagged with `<tags>` in `<exp_name>` space.
`<tags>` must be specified with double quotes (e.g., `$ tagit record myexp "a=1, b=2", -- ./run_exp.sh`).
The data category into which data is recorded can be specified using `-d` option; the default category is `raw`.
`-s` option is for choosing the stream to record (`stdout, stderr, all (default)`).


#### 2. `report`
```
$ tagit report <exp_name> [<tags>] [-c <csv_file>] [-f <path>] [-d <data_category>]
```
Reports the data in `<exp_name>` space.
If <tags> are specified, tagit reports data corresponding to the specified tags.
By default, the result is printed in terminal.
Data category to be reported can be specified using `-d` option, and all data categories are reported by default. 
  
* Multi-valued tags
  - Users can choose multiple tag values at a time using the operator `|`.
  - Example: `"color=red|blue, shape=cube"`

* Tag order
  - Users can specify the tag order in `<tag>`. For example, `"c=3, b=2, a=1"` makes tags printed in c-b-a order.
  - Also, tag can be specified without values like `"c, b=2, a"`.
  This is for setting the tag order without changing the report scope.

* Result format options
  - `-c`: Print the result in csv format
  - `-f`: Print the result in file hierarchy; each data is saved as a file under the nested directory path, where each directory corresponds to a tag
  
  
#### 3. `parse`
##### 3.1. `parse add`
```
$ tagit parse add <exp_name> [-s <src_category>] <dest_category> <rule>
```
Add a parsing rule to an experiment `<exp_name>`.
For each data in experiment `<exp_name>`, `<rule>` is applied to `raw` category, and the result is saved in `<dest_category>`.
If `<src_category>` is specified, the `<rule>` is applied to `<src_category>`.
The `<rule>` should follow shell command format (For example: `awk '^latency/{print \$NF}'`).

##### 3.2. `parse list`
```
$ tagit parse list <exp_name>
```
List parsing rules in the experiment `<exp_name>`.

##### 3.3. `parse remove`
```
$ tagit parse remove <exp_name> [-a] [<rule_id>]
```
Remove parsing rule of id `<rule_id>:` from the experiment `<exp_name>`.
If `-a` is specified, all parsing rules are removed.

#### 4. `manage`
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
List the experiments. If `<exp_name>` is specified, it lists the name of tags and data categories in the specified experiment instead.


#### 2. `export`
```
$ tagit export <output_dump>
```
Export all experiment and data to `<output_dump>`.


#### 3. `import`
```
$ tagit import <db_dump>
```
Import experiments and data from `<db_dump>`.


#### 4. `reset`
```
$ tagit reset [-y]
```
Reset tagit database. `-y` passes all yes to prompts automatically.


## Notes
This tools is currently alpha version and may contain lots of bugs.
Issues & pull requests about new features, bug reports are appreciated.
