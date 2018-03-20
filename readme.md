# miRLocator 项目说明

### 环境说明

请参看docker里面的环境

要定时清理 upload 和 static/results 里的数据，否则会比较占空间

### 部署说明

进入项目的目录
`cd project_root`

----

安装依赖
`apt-get install uwsgi nginx supervisor uwsgi-plugin-python`

----

`vi /etc/nginx/conf.d/mirlocator.conf`

添加如下内容：

{example.com} 为你的域名

{/var/www/example.com} 为你的项目路径

```
server {
	listen 80;
	listen [::]:80;

	server_name {example.com};

	root {/var/www/example.com};
	index index.html;

    location / { try_files $uri @mirlocator; }
    location @mirlocator {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/mirlocator.sock;
    }
}
```

----

`vi uwsgi.ini`

内容如下：

```
[uwsgi]

socket = 127.0.0.1:6001

module = main:app

processes = 4

threads = 2

plugins = python
```

----

`vi /etc/supervisor/conf.d/mirlocator.conf`

内容如下：
````
[program:mirlocator]
command=uwsgi  /var/www/mirlocator/uwsgi.ini

directory=/var/www/mirlocator
user=root

autostart=true
autorestart=true
startretries=3
stdout_logfile=/var/log/mirlocator_out.log
stderr_logfile=/var/log/mirlocator_err.log
````

`service nginx restart`

`service supervisor restart`
