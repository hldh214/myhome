import frida


def on_message(message, data):
    if message['type'] == 'send':
        print("[*] {0}".format(message['payload']), data)
    else:
        print(message, data)


js_code = """
Java.perform(function () {
  var ConsumerIrManager = Java.use('android.hardware.ConsumerIrManager');
  ConsumerIrManager.transmit.implementation = function (...params) {
    send('hook success');
    console.log('params: ' + params);

    return this.transmit(...params);
  };
});
"""

# frida-ps -U
# https://github.com/frida/frida/releases/download/16.0.6/frida-server-16.0.6-android-arm.xz
# ./adb push ..\..\frida-server-16.0.6-android-arm\frida-server-16.0.6-android-arm '/data/local/tmp/'
# chmod +x /data/local/tmp/frida-server-16.0.6-android-arm
# /data/local/tmp/frida-server-16.0.6-android-arm

# process = frida.get_usb_device().attach('遥控精灵')
process = frida.get_usb_device().attach('遥控专家酷控')

script = process.create_script(js_code)

script.on('message', on_message)
print('[*] Hook Start Running')
script.load()
input('[*] Press Enter to exit...')
