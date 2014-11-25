# Steaming for Taiwan Radio

## Requirement

  * python 2.7.8

## Execution

See list of radio first by`./pyradio.py --list`, and remember the radio id you want to listen to.

Use following command to record radio into a file.
```bash
$ python pytwradio.py --id 370 -t 100 -o output.ts
# -t recording time(s) or using `-t -1' to endless record
```

On mac, you can use the following command to play radio
```bash
$ ./pytwradio.py --id 370 -t -1 -o output.ts 2>/dev/null & sleep 10 && ffplay output.ts
```

Record audio with playing video 
```bash
$ ./pytwradio.py --id 370 -t -1 --play [-o output.ts]
```
