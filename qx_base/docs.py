description = """
# Auth

获取服务端 token, 需要认证的请求在 http 的 header 中添加 MYAUTHORIZATION 参数:

    MYAUTHORIZATION: token <value>

# API 相关信息

Http status:

* 2xx: 正确
* 3xx: 重定向
* 4xx: 接口相关错误, 后台程序返回的错误
* 5xx: 后台服务器报错, 需要联系后台开发人员或者运维

JsonResponse Code:

* 200  正确返回
* 4000 普通返回显示错误
* 4001 用户认证错误
* 4002 接口签名错误
* 4003 token过期
* 4004 资源未找到
* 4005 用户被禁用
* 4006 内容不合法
* 4007 请求对应字段错误 (添加detail参数)
* 4013 用户没有操作权限
* 4014 网络错误
* 5000 服务器错误
"""  # noqa
