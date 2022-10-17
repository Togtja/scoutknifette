# scoutknifette

## Usage

`python3 scout_knife.py NameOfTaxa`
Though it is meant to run in the background so it can be smart running it in detached:
`python3 scout_knife.py NameOfTaxa &`
And then It might be smart to the output to a file so:
`python3 scout_knife.py NameOfTaxa &> scout_knife_log.txt`

## Config

To use the config you have to create a `.config` file in the working directory. Below desibes the different parameters you can add to the config file. There is also an example config file in this repo called `.config_example`

### webhook_url

Default Value: `None`
Example in `.config`: `webhook_url=https://discord.com/api/webhooks/{webhook_id}/{token}`

The config is very basic and just change some of it parameters, the only one that does not have a default value is `webhook_url` so that one should be set if you want to support logging to a webhook.

The request is a `POST` request	 with this header:

```json
{
    "method": 'POST',
    "Content-Type": "application/json"
}
```

and with this as json body:

```json
{
    "content": message
}
```

where `message` is a string from the script that it want to report typically errors or starting and ending of a batch

At the moment it is only tested with the discord webhook api.

### max_size

Default value: `10`
Example in `.config`: `max_size=10`

This is how many sub_process to run concurrently.

### sub_process

Default value: `1`
Example in `.config`: `sub_process=1`

This is the starting point of the id of the sub process

### max_sub_process

Default value: `100`
Example in `.config`: `max_sub_process=100`

So it will create a process with id starting from `sub_process` and it will run `max_size` at the time. When the process id hits `max_size` it will stop creating more process and eventually exit, when all its sub_process has completed.

### sleep_time

Default value: `108000` (30 minutes)
Example in `.config`: `sleep_time=108000`

How long in seconds it will sleep in between checks to see if the processes are still running and spawn new once.
