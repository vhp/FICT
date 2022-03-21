# FICT is a simple file integrity checking tool.


Basic usage is as follows.
```
cd ~
fict init
fict add ~/Documents
fict list
fict compute
fict check
```

The database will is stored in `~/.fict`. The fict_db file that's normally in `~/.fict`
can be manipulated manually. The changes will be ingested upon next run.

The location of where the `fict_db` can be stored can be specified with the option
`--fict-dir`.

If you don't specify a location the present working directory will be chosen.


`--hash-tool` defaults to sha512sum. Though you can pass in whatever tool you
want to use. Some options are b2sum, md5sum, sha1sum, crc32. Use the tool that
you feel best about. md5sum is available everywhere and is a good middleground.
b2sum is faster but not as available. crc32 is simple but may take longer than
all even though it's supposed to be faster. Note that if your fict-db is defined
to use one tool and you change it. The software will get
confused.
