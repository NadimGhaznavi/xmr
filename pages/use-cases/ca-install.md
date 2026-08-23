



```
root@paris:~ # git clone git@github.com:NadimGhaznavi/bmca
Cloning into 'bmca'...
remote: Enumerating objects: 650, done.
remote: Counting objects: 100% (359/359), done.
remote: Compressing objects: 100% (198/198), done.
remote: Total 650 (delta 199), reused 289 (delta 134), pack-reused 291 (from 1)
Receiving objects: 100% (650/650), 4.00 MiB | 586.00 KiB/s, done.
Resolving deltas: 100% (344/344), done.
root@paris:~ # 
```

root@paris:~/bmca # ./scripts/install.sh --environment prod
[SUCCESS] Installed bmca 0.2.37 for prod. Initialize or restore the CA before enabling the service.
root@paris:~ # 
```

```
root@paris:~/bmca # ./scripts/initialize-ca.sh offline --environment prod --workspace /root/bmca-workspace

Generating root certificate... done!
Generating intermediate certificate... done!
Generating user and host SSH certificate signing keys... done!

✔ Root certificate: /root/bmca-workspace/certs/root_ca.crt
✔ Root private key: /root/bmca-workspace/secrets/root_ca_key
✔ Root fingerprint: c0652f7ebc068414e6cc09f56563b48e4df64c0d788d70678feea8ab9aa4fd80
✔ Intermediate certificate: /root/bmca-workspace/certs/intermediate_ca.crt
✔ Intermediate private key: /root/bmca-workspace/secrets/intermediate_ca_key
✔ SSH user public key: /root/bmca-workspace/certs/ssh_user_ca_key.pub
✔ SSH user private key: /root/bmca-workspace/secrets/ssh_user_ca_key
✔ SSH host public key: /root/bmca-workspace/certs/ssh_host_ca_key.pub
✔ SSH host private key: /root/bmca-workspace/secrets/ssh_host_ca_key
✔ Database folder: /root/bmca-workspace/db
✔ Templates folder: /root/bmca-workspace/templates
✔ Default configuration: /root/bmca-workspace/config/defaults.json
✔ Certificate Authority configuration: /root/bmca-workspace/config/ca.json

Your PKI is ready to go. To generate certificates for individual services see 'step help ca'.

FEEDBACK 😍 🍻
  The step utility is not instrumented for usage statistics. It does not phone
  home. But your feedback is extremely valuable. Any information you can provide
  regarding how you’re using `step` helps. Please send us a sentence or two,
  good or bad at feedback@smallstep.com or join GitHub Discussions
  https://github.com/smallstep/certificates/discussions and our Discord 
  https://u.step.sm/discord.
[SUCCESS] Offline PKI created in /root/bmca-workspace. Keep it offline.
[SUCCESS] Online transfer bundle: /root/bmca-workspace-online-prod.tar
[SUCCESS] Ceremony manifest: /root/bmca-workspace-online-prod.tar.manifest
root@paris:~/bmca # ls
```