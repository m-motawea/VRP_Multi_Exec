from datetime import datetime
import paramiko
import gevent
import socket


class BaseConnection(object):
    def __init__(self, ip, username, password=None, key_path=None, hostname=""):
        """Base ssh connection object.

        Args:
            ip (str): host ip to connect to.
            username (str): username for auth.
            password (str, optional): password for auth. Defaults to None.
            key_path (str, optional): path to private key file for auth. Defaults to None.
            hostname (str, optional): hostname. Defaults to "".
        """
        self.ip = ip
        self.password = password
        self.key_path = key_path
        if not any([self.password, self.key_path]) or all(
            [self.password, self.key_path]
        ):
            raise Exception("must pass only one of key_path or password")
        self.username = username
        self.hostname = hostname
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.password:
                self.client.connect(
                    hostname=self.ip, username=self.username, password=self.password
                )
            elif self.key_path:
                self.client.connect(
                    hostname=self.ip, key_filename=self.key_path, username=self.username
                )
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
    def shell_wait(shell, timeout, stderr=False):
        now = datetime.now().timestamp()
        while datetime.now().timestamp() < now + timeout:
            if stderr:
                if shell.recv_stderr_ready():
                    break
            else:
                if shell.recv_ready():
                    break
            gevent.sleep(1)

    @staticmethod
    def shell_exec(shell, command, timeout=2):
        def recv_stdout():
            output = ""
            BaseConnection.shell_wait(shell, timeout)
            try:
                buffer = shell.recv(1024).decode()
            except socket.timeout:
                buffer = None
            while buffer:
                output += str(buffer)
                try:
                    buffer = shell.recv(1024).decode()
                except socket.timeout:
                    buffer = None
            return output

        def recv_stderr():
            error = ""
            BaseConnection.shell_wait(shell, timeout, stderr=True)
            try:
                buffer = shell.recv_stderr(1024).decode()
            except socket.timeout:
                buffer = None
            while buffer:
                error += str(buffer)
                try:
                    buffer = shell.recv_stderr(1024).decode()
                except socket.timeout:
                    buffer = None
            return error

        shell.settimeout(timeout)
        if not command.endswith("\n"):
            command += "\n"

        shell.send(command)
        stderr_thread = gevent.spawn(recv_stderr)
        stdout_thread = gevent.spawn(recv_stdout)
        gevent.joinall([stdout_thread, stderr_thread])
        output = stdout_thread.value
        error = stderr_thread.value
        return output, error

    def close(self):
        self.client.close()


class NetworkDeviceConnection(BaseConnection):
    def __init__(self, ip, username, password, key_path, hostname):
        """Ssh connection object for network devices.

        Args:
            ip (str): host ip to connect to.
            username (str): username for auth.
            password (str, optional): password for auth. Defaults to None.
            key_path (str, optional): path to private key file for auth. Defaults to None.
            hostname (str, optional): hostname. Defaults to "".

        Raises:
            Exception:
        """
        super().__init__(
            ip, username, password=password, key_path=key_path, hostname=hostname
        )
        self.shell = None

    def connect(self):
        client = super().connect()
        self.shell = self.get_shell()
        return client

    def exec(self, command, timeout):
        return self.shell_exec(self.shell, command, timeout)
