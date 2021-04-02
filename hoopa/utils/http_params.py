"""
主要用于在中间件设置request参数，主要是aiohttp和httpx的请求参数老是记不住，每次都去看源码又太麻烦
例如：request.set(AiohttpRequest.allow_redirects, False)
"""


class AiohttpRequest:
    """
        aiohttp request参数

        method: str,
        str_or_url: StrOrURL,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        cookies: Optional[LooseCookies] = None,
        headers: Optional[LooseHeaders] = None,
        skip_auto_headers: Optional[Iterable[str]] = None,
        auth: Optional[BasicAuth] = None,
        allow_redirects: bool = True,
        max_redirects: int = 10,
        compress: Optional[str] = None,
        chunked: Optional[bool] = None,
        expect100: bool = False,
        raise_for_status: Optional[bool] = None,
        read_until_eof: bool = True,
        proxy: Optional[StrOrURL] = None,
        proxy_auth: Optional[BasicAuth] = None,
        timeout: Union[ClientTimeout, object] = sentinel,
        verify_ssl: Optional[bool] = None,
        fingerprint: Optional[bytes] = None,
        ssl_context: Optional[SSLContext] = None,
        ssl: Optional[Union[SSLContext, bool, Fingerprint]] = None,
        proxy_headers: Optional[LooseHeaders] = None,
        trace_request_ctx: Optional[SimpleNamespace] = None,
        read_bufsize: Optional[int] = None,
    """
    method = "method"
    str_or_url = "str_or_url"
    params = "params"
    data = "data"
    json = "json"
    cookies = "cookies"
    headers = "headers"
    skip_auto_headers = "skip_auto_headers"
    auth = "auth"
    allow_redirects = "allow_redirects"
    max_redirects = "max_redirects"
    compress = "compress"
    chunked = "chunked"
    expect100 = "expect100"
    raise_for_status = "raise_for_status"
    read_until_eof = "read_until_eof"
    proxy = "proxy"
    proxy_auth = "proxy_auth"
    timeout = "timeout"
    verify_ssl = "verify_ssl"
    fingerprint = "fingerprint"
    ssl_context = "ssl_context"
    ssl = "ssl"
    proxy_headers = "proxy_headers"
    trace_request_ctx = "trace_request_ctx"
    read_bufsize = "read_bufsize"


class AiohttpClient:
    """
        aiohttp ClientSession参数

        connector: Optional[BaseConnector] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        cookies: Optional[LooseCookies] = None,
        headers: Optional[LooseHeaders] = None,
        skip_auto_headers: Optional[Iterable[str]] = None,
        auth: Optional[BasicAuth] = None,
        json_serialize: JSONEncoder = json.dumps,
        request_class: Type[ClientRequest] = ClientRequest,
        response_class: Type[ClientResponse] = ClientResponse,
        ws_response_class: Type[ClientWebSocketResponse] = ClientWebSocketResponse,
        version: HttpVersion = http.HttpVersion11,
        cookie_jar: Optional[AbstractCookieJar] = None,
        connector_owner: bool = True,
        raise_for_status: bool = False,
        read_timeout: Union[float, object] = sentinel,
        conn_timeout: Optional[float] = None,
        timeout: Union[object, ClientTimeout] = sentinel,
        auto_decompress: bool = True,
        trust_env: bool = False,
        requote_redirect_url: bool = True,
        trace_configs: Optional[List[TraceConfig]] = None,
        read_bufsize: int = 2  16,
    """
    connector = "connector"
    loop = "loop"
    cookies = "cookies"
    headers = "headers"
    skip_auto_headers = "skip_auto_headers"
    auth = "auth"
    json_serialize = "json_serialize"
    request_class = "request_class"
    response_class = "response_class"
    ws_response_class = "ws_response_class"
    version = "version"
    cookie_jar = "cookie_jar"
    connector_owner = "connector_owner"
    raise_for_status = "raise_for_status"
    read_timeout = "read_timeout"
    conn_timeout = "conn_timeout"
    timeout = "timeout"
    auto_decompress = "auto_decompress"
    trust_env = "trust_env"
    requote_redirect_url = "requote_redirect_url"
    trace_configs = "trace_configs"
    read_bufsize = "read_bufsize"


class HttpxRequest:
    """
        * method - HTTP method for the new `Request` object: `GET`, `OPTIONS`,
        `HEAD`, `POST`, `PUT`, `PATCH`, or `DELETE`.
        * url - URL for the new `Request` object.
        * params - *(optional)* Query parameters to include in the URL, as a
        string, dictionary, or sequence of two-tuples.
        * content - *(optional)* Binary content to include in the body of the
        request, as bytes or a byte iterator.
        * data - *(optional)* Form data to include in the body of the request,
        as a dictionary.
        * files - *(optional)* A dictionary of upload files to include in the
        body of the request.
        * json - *(optional)* A JSON serializable object to include in the body
        of the request.
        * headers - *(optional)* Dictionary of HTTP headers to include in the
        request.
        * cookies - *(optional)* Dictionary of Cookie items to include in the
        request.
        * auth - *(optional)* An authentication class to use when sending the
        request.
        * proxies - *(optional)* A dictionary mapping proxy keys to proxy URLs.
        * timeout - *(optional)* The timeout configuration to use when sending
        the request.
        * allow_redirects - *(optional)* Enables or disables HTTP redirects.
        * verify - *(optional)* SSL certificates (a.k.a CA bundle) used to
        verify the identity of requested hosts. Either `True` (default CA bundle),
        a path to an SSL certificate file, or `False` (disable verification).
        * cert - *(optional)* An SSL certificate used by the requested host
        to authenticate the client. Either a path to an SSL certificate file, or
        two-tuple of (certificate file, key file), or a three-tuple of (certificate
        file, key file, password).
        * trust_env - *(optional)* Enables or disables usage of environment
        variables for configuration.
    """
    
    method = "method"
    url = "url"
    params = "params"
    content = "content"
    data = "data"
    files = "files"
    json = "json"
    headers = "headers"
    cookies = "cookies"
    auth = "auth"
    proxies = "proxies"
    timeout = "timeout"
    allow_redirects = "allow_redirects"
    verify = "verify"
    cert = "cert"
    trust_env = "trust_env"


class HttpxClient:
    """
        httpx.AsyncClient()的参数

         Parameters:
            *  auth  - *(optional)* An authentication class to use when sending
            requests.
            *  params  - *(optional)* Query parameters to include in request URLs, as
            a string, dictionary, or sequence of two-tuples.
            *  headers  - *(optional)* Dictionary of HTTP headers to include when
            sending requests.
            *  cookies  - *(optional)* Dictionary of Cookie items to include when
            sending requests.
            *  verify  - *(optional)* SSL certificates (a.k.a CA bundle) used to
            verify the identity of requested hosts. Either `True` (default CA bundle),
            a path to an SSL certificate file, or `False` (disable verification).
            *  cert  - *(optional)* An SSL certificate used by the requested host
            to authenticate the client. Either a path to an SSL certificate file, or
            two-tuple of (certificate file, key file), or a three-tuple of (certificate
            file, key file, password).
            *  http2  - *(optional)* A boolean indicating if HTTP/2 support should be
            enabled. const to `False`.
            *  proxies  - *(optional)* A dictionary mapping HTTP protocols to proxy
            URLs.
            *  timeout  - *(optional)* The timeout configuration to use when sending
            requests.
            *  limits  - *(optional)* The limits configuration to use.
            *  max_redirects  - *(optional)* The maximum number of redirect responses
            that should be followed.
            *  base_url  - *(optional)* A URL to use as the base when building
            request URLs.
            *  transport  - *(optional)* A transport class to use for sending requests
            over the network.
            *  app  - *(optional)* An ASGI application to send requests to,
            rather than sending actual network requests.
            *  trust_env  - *(optional)* Enables or disables usage of environment
            variables for configuration.
    """
    auth = "auth"
    params = "params"
    headers = "headers"
    cookies = "cookies"
    verify = "verify"
    cert = "cert"
    http2 = "http2"
    proxies = "proxies"
    mounts = "mounts"
    timeout = "timeout"
    limits = "limits"
    pool_limits = "pool_limits"
    max_redirects = "max_redirects"
    event_hooks = "event_hooks"
    base_url = "base_url"
    transport = "transport"
    app = "app"
    trust_env = "trust_env"
