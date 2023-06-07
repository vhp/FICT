# FICT is a simple file integrity checking tool.

## Usage
Basic usage is as follows.
```
cd ~
fict init
fict add ~/Documents
fict list
fict compute
fict check
```

The database will is stored in `~/.fict/fict_db`. The fict_db file that's normally in `~/.fict`
can be manipulated manually. The changes will be ingested upon next run.

The location of where the `fict_db` can be stored can be specified with the option
`--fict-dir`. The default is in your `$HOME`

`--hash-tool` defaults to sha512sum. Though you can pass in whatever tool you
want to use. Some options are b2sum, md5sum, sha1sum, crc32. Use the tool that
you feel best about. md5sum is available everywhere and is a good middle ground.
b2sum is faster but not as available. We do a b2sum on every file by default but
this can also be adjusted via `--default-hash-tool`. crc32 is simple but may take longer than
all even though it's supposed to be faster. crc32 is meant for short
communication verification rather than a 27GB mp4.

**Note** that if your fict-db is defined to use one tool and you change it
after the fact. The software will get confused. In that case it's recommended
you open the fict_db file and use a tool like `sed(1)` to change all occurrences.

The fict_db is written out every so often. At the time of writing this at
around every 1000 computations. This can be changed in the code but it's not at
the moment a cli parameter. The bigger the number the more potential lost work
you can have if your system crashes. The shorter the number the more churn on
your disk.

If you notice any bugs feel free to email me.

**Note** I use a Linux desktop so that's what I run this on. There may need to be adapting to get it to work on Macs.

## Installing
`pip install Fict`

You can also clone the code from [github](https://github.com/vhp/FICT) and run
the fict command.

## Publishing to Pypi

```
pip install twine
python3 setup.py sdist
twine upload dist/*
```
