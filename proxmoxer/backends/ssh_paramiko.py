__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"

# spell-checker:ignore putfo

import os

from proxmoxer.backends.base import BaseBackend, BaseSession
from proxmoxer.backends.utils import shelljoin

try:
    import paramiko
except ImportError:
    import sys

    sys.stderr.write("Chosen backend requires 'paramiko' module\n")
    sys.exit(1)


class SshParamikoSession(BaseSession):
    def __init__(self, host, user, password=None, private_key_file=None, port=22, **kwargs):
        super(SshParamikoSession, self).__init__(**kwargs)
        self.host = host
        self.user = user
        self.password = password
        self.private_key_file = private_key_file
        self.port = port

        self.ssh_client = self._connect()

    def _connect(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.private_key_file:
            key_filename = os.path.expanduser(self.private_key_file)
        else:
            key_filename = None

        ssh_client.connect(
            self.host,
            username=self.user,
            allow_agent=(not self.password),
            look_for_keys=True,
            key_filename=key_filename,
            password=self.password,
            timeout=self.timeout,
            port=self.port,
        )

        return ssh_client

    def _exec(self, cmd):
        session = self.ssh_client.get_transport().open_session()
        session.exec_command(shelljoin(cmd))
        stdout = session.makefile("rb", -1).read().decode()
        stderr = session.makefile_stderr("rb", -1).read().decode()
        return stdout, stderr

    def upload_file_obj(self, file_obj, remote_path):
        sftp = self.ssh_client.open_sftp()
        sftp.putfo(file_obj, remote_path)
        sftp.close()


class Backend(BaseBackend):
    def __init__(self, *args, **kwargs):
        self.session = SshParamikoSession(*args, **kwargs)
