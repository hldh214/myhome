import myhome

config = myhome.get_config()


def power_con(s):
    l = [int(x) for x in s.split(',')]
    l = [x if i % 2 == 0 else -x for i, x in enumerate(l)]
    return ','.join([str(x) for x in l])


for infrared in config['infrared']['single']:
    print(f'{infrared["command"]}[{infrared["params"][0]}]: {power_con(infrared["params"][1])}')
