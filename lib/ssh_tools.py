from datetime import datetime, time
import paramiko
import gevent

class BaseConnection(object):
    def __init__(self, ip, username, password=None, key_path=None, hostname=""):
        self.ip = ip
        self.password = password
        self.key_path = key_path
        if not any([self.password, self.key_path]) or all([self.password, self.key_path]):
            raise Exception("must pass only one of key_path or password")
        self.username = username
        self.hostname = hostname
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.password:
                self.client.connect(hostname=self.ip, username=self.username, password=self.password)
            elif self.key_path:
                self.client.connect(hostname=self.ip, key_filename=self.key_path, username=self.username)
        except Exception as e:
            print("failed to connect due to exception: {}".format(str(e)))
            return False
        return True

    def get_shell(self):
        return self.client.invoke_shell()

    def exec_cmd(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        stdin.close()
        err = stderr.read()
        out = stdout.read()
        stderr.close()
        stdout.close()
        if stderr:
            return False, err.decode()
        return True, out.decode()

    @staticmethod
    def shell_wait(shell, timeout):
        now = datetime.now().timestamp()
        while datetime.now().timestamp() < now + timeout:
            if shell.recv_ready():
                break
            gevent.sleep(1)

    @staticmethod
    def shell_exec(shell, command, timeout=2):
        output = ""
        shell.settimeout(timeout)
        shell.send(command + "\n")
        BaseConnection.shell_wait(shell, timeout)
        buffer = shell.recv(1024).decode()
        while buffer:
            output += str(buffer)
            try:
                buffer = shell.recv(1024).decode()
            except:
                buffer = None
        return output

    def close(self):
        self.client.close()
        
