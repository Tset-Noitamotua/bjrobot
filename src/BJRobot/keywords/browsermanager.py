import os
import robot.utils
from robot.errors import DataError
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from browsercache import BrowserCache
from keywordgroup import KeywordGroup
from BJRobot.utilities import System

BROWSER_NAMES = {'ff': "_make_ff",
                 'firefox': "_make_ff",
                 'ie': "_make_ie",
                 'internetexplorer': "_make_ie",
                 'googlechrome': "_make_chrome",
                 'gc': "_make_chrome",
                 'chrome': "_make_chrome",
                 'opera': "_make_opera",
                 'phantomjs': "_make_phantomjs",
                 'htmlunit': "_make_htmlunit",
                 'htmlunitwithjs': "_make_htmlunitwithjs",
                 'android': "_make_android",
                 'iphone': "_make_iphone",
                 'safari': "_make_safari",
                 'edge': "_make_edge"
                 }


class BrowserManager(KeywordGroup):
    __chromeDriverVersion = "2.27"
    __EdgeDriverVersion = "14393"
    __firefoxDriverVersion = "0.12"
    __ieDriverVersion = "2.53"

    def __init__(self):
        self._cache = BrowserCache()
        self._default_script_timeout_in_secs = 10
        self._default_implicit_wait_in_secs = 20

    def open_browser(self, url, browser_name="chrome", proxy=None, alias=None):
        try:
            driver_instance = self._make_browser(browser_name, proxy)
            driver_instance.get(url)
        except:
            raise
        self._cache.register(driver_instance, alias)

    def close_all_browsers(self):
        self._cache.close_all()

    def close_browser(self):
        """Closes the current browser."""
        if self._cache.current:
            self._cache.close()

    def switch_browser(self, index_or_alias):
        """Switches between active browsers using index or alias.

                Index is returned from `Open Browser` and alias can be given to it.

                Example:
                | Open Browser        | http://google.com | ff       |
                | URL Should Be  | http://google.com |          |
                | Open Browser        | http://yahoo.com  | ie       | 2nd conn |
                | URL Should Be  | http://yahoo.com  |          |
                | Switch Browser      | 1                 | # index  |
                | Page Should Contain | I'm feeling lucky |          |
                | Switch Browser      | 2nd conn          | # alias  |
                | Page Should Contain | More Yahoo!       |          |
                | Close All Browsers  |                   |          |

                Above example expects that there was no other open browsers when
                opening the first one because it used index '1' when switching to it
                later. If you aren't sure about that you can store the index into
                a variable as below.

                | ${id} =            | Open Browser  | http://google.com | *firefox |
                | # Do something ... |
                | Switch Browser     | ${id}         |                   |          |
                """
        try:
            self._cache.switch(index_or_alias)
        except (RuntimeError, DataError):  # RF 2.6 uses RE, earlier DE
            raise RuntimeError("No browser with index or alias '%s' found." % index_or_alias)

    def maximize_browser_window(self):
        """Maximizes current browser window."""
        self._current_browser().maximize_window()

    def set_window_size(self, width, height):
        """Sets the `width` and `height` of the current window to the specified values.

                Example:
                | Set Window Size | ${800} | ${600}       |
                | ${width} | ${height}= | Get Window Size |
                | Should Be Equal | ${width}  | ${800}    |
                | Should Be Equal | ${height} | ${600}    |
                """
        return self._current_browser().set_window_size(width, height)

    def get_window_size(self):
        """Returns current window size as `width` then `height`.

        Example:
        | ${width} | ${height}= | Get Window Size |
        """
        size = self._current_browser().get_window_size()
        return size['width'], size['height']

    def get_url(self):
        """Returns the current location."""
        return self._current_browser().current_url

    def url_should_be(self, url):
        """Verifies that current URL is exactly `url`."""
        actual = self.get_url()
        if actual != url:
            raise AssertionError("Location should have been '%s' but was '%s'"
                                 % (url, actual))

    def url_should_contain(self, expected):
        """Verifies that current URL contains `expected`."""
        actual = self.get_url()
        if expected not in actual:
            raise AssertionError("Location should have contained '%s' "
                                 "but it was '%s'." % (expected, actual))

    def get_title(self):
        """Returns title of current page."""
        return self._current_browser().title

    def title_should_be(self, title):
        """Verifies that current page title equals `title`."""
        actual = self.get_title()
        if actual != title:
            raise AssertionError("Title should have been '%s' but was '%s'"
                                 % (title, actual))

    def title_should_contain(self, expected):
        """Verifies that current page title equals `title`."""
        actual = self.get_title()
        if expected not in actual:
            raise AssertionError("Title should have contained '%s' but was '%s'"
                                 % (expected, actual))

    def go_back(self):
        """Simulates the user clicking the "back" button on their browser."""
        self._current_browser().back()

    def go_to(self, url):
        """Navigates the active browser instance to the provided URL."""
        self._current_browser().get(url)

    def reload_page(self):
        """Simulates user reloading page."""
        self._current_browser().refresh()

    def accept_alert(self):
        self._current_browser().switch_to().alert().accept()

    def dismiss_alert(self):
        self._current_browser().switch_to().alert().dismiss()

    def authenticate_alert(self):
        self._current_browser().switch_to.alert.authenticate()

    def set_browser_implicit_wait(self, seconds):
        implicit_wait_in_secs = robot.utils.timestr_to_secs(seconds)
        self._current_browser().implicitly_wait(implicit_wait_in_secs)

    def set_browser_script_timeout(self, seconds):
        """Sets the timeout in seconds used by various keywords.

        There are several `Wait ...` keywords that take timeout as an
        argument. All of these timeout arguments are optional. The timeout
        used by all of them can be set globally using this keyword.
        See `Timeouts` for more information about timeouts.

        The previous timeout value is returned by this keyword and can
        be used to set the old value back later. The default timeout
        is 5 seconds, but it can be altered in `importing`.

        Example:
        | ${orig timeout} = | Set Selenium Timeout | 15 seconds |
        | Open page that loads slowly |
        | Set Selenium Timeout | ${orig timeout} |
        """
        _timeout_in_secs = robot.utils.timestr_to_secs(seconds)
        self._current_browser().set_script_timeout(_timeout_in_secs)

    def set_global_script_timeout(self, seconds):
        """
        Example:
        | ${orig timeout} = | Set Selenium Timeout | 15 seconds |
        | Open page that loads slowly |
        | Set Selenium Timeout | ${orig timeout} |
        """
        old_timeout = self._default_script_timeout_in_secs
        self._default_script_timeout_in_secs = robot.utils.timestr_to_secs(seconds)
        for driver_instance in self._cache.get_open_browsers():
            driver_instance.set_script_timeout(self._default_script_timeout_in_secs)
        return old_timeout

    def set_global_implicit_wait(self, seconds):
        """
        Example:
        | ${orig wait} = | Set Selenium Implicit Wait | 10 seconds |
        | Perform AJAX call that is slow |
        | Set Selenium Implicit Wait | ${orig wait} |
        """
        old_wait = self._default_implicit_wait_in_secs
        self._default_implicit_wait_in_secs = robot.utils.timestr_to_secs(seconds)
        for driver_instance in self._cache.get_open_browsers():
            driver_instance.implicitly_wait(self._default_implicit_wait_in_secs)
        return old_wait

    def _current_browser(self):
        if not self._cache.current:
            raise RuntimeError('No browser is open')
        return self._cache.current

    def _get_browser_creation_function(self, browser_name):
        func_name = BROWSER_NAMES.get(browser_name.lower().replace(' ', ''))
        return getattr(self, func_name) if func_name else None

    def _make_browser(self, browser_name, proxy=None):
        creation_func = self._get_browser_creation_function(browser_name)
        if not creation_func:
            raise ValueError(browser_name + " is not a supported browser.")
        driver_instance = creation_func(proxy)

        driver_instance.set_script_timeout(self._default_script_timeout_in_secs)
        driver_instance.implicitly_wait(self._default_implicit_wait_in_secs)
        return driver_instance

    def _make_ff(self, proxy=None):
        cur_path = os.path.split(os.path.realpath(__file__))[0]
        cur_path = cur_path + os.sep + ".." + os.sep + 'log' + os.sep + 'geckodriver.log'
        fp = None
        if System.get_os_name().lower() == 'windows':
            target = os.path.expanduser('~') \
                     + os.sep + 'AppData' + os.sep + 'Roaming' + os.sep + 'Mozilla' + os.sep + 'Firefox' \
                     + os.sep + 'Profiles'
            fp = System.search_file_contains(target, '.default')
        firefox_profile = webdriver.FirefoxProfile(fp)
        if proxy is not None:
            host, port = proxy.split(r'//')[1].split(':')[0], proxy.split(r'//')[1].split(':')[1]

            firefox_profile.set_preference("network.proxy.http", host)
            firefox_profile.set_preference("network.proxy.http_port", int(port))
            firefox_profile.set_preference("network.proxy.ssl", host)
            firefox_profile.set_preference("network.proxy.ssl_port", int(port))
            firefox_profile.set_preference("network.proxy.socks", host)
            firefox_profile.set_preference("network.proxy.socks_port", int(port))
            firefox_profile.set_preference("network.proxy.ftp", host)
            firefox_profile.set_preference("network.proxy.ftp_port", int(port))
            firefox_profile.set_preference("network.proxy.no_proxies_on", 'localhost')
            firefox_profile.set_preference("network.proxy.type", 1)
        else:
            firefox_profile.set_preference("network.proxy.type", 0)
        firefox_capabilities = DesiredCapabilities.FIREFOX
        firefox_capabilities['acceptInsecureCerts'] = True
        firefox_capabilities['marionette'] = True

        binary = FirefoxBinary()

        return webdriver.Firefox(executable_path=self.__get_driver_path("firefox"), capabilities=firefox_capabilities,
                                 firefox_binary=binary, firefox_profile=firefox_profile, log_path=cur_path)

    def _make_ie(self, proxy=None):
        cur_path = os.path.split(os.path.realpath(__file__))[0]
        cur_path = cur_path + os.sep + ".." + os.sep + 'log' + os.sep + 'ie.log'
        ie_capabilities = DesiredCapabilities.INTERNETEXPLORER
        ie_capabilities['ignoreProtectedModeSettings'] = True
        ie_capabilities['INTRODUCE_FLAKINESS_BY_IGNORING_SECURITY_DOMAINS'] = True
        ie_capabilities['requireWindowFocus'] = False
        ie_capabilities['enableElementCacheCleanup'] = True
        ie_capabilities['ie.usePerProcessProxy'] = True
        ie_capabilities['proxy'] = System.set_proxy(proxy)
        return webdriver.Ie(executable_path=self.__get_driver_path("ie"),
                            capabilities=ie_capabilities, log_file=cur_path, log_level='INFO')

    def _make_chrome(self, proxy=None):
        cur_path = os.path.split(os.path.realpath(__file__))[0]
        cur_path = cur_path + os.sep + ".." + os.sep + 'log' + os.sep + 'chrome.log'
        chrome_capabilities = webdriver.DesiredCapabilities.CHROME
        chrome_capabilities['chromeOptions'] = {"args": ["--disable-extensions"], "extensions": []}
        chrome_capabilities['proxy'] = System.set_proxy(proxy)
        return webdriver.Chrome(executable_path=self.__get_driver_path("chrome"),
                                desired_capabilities=chrome_capabilities, service_log_path=cur_path)

    def _make_edge(self, proxy=None):
        if hasattr(webdriver, 'Edge'):
            cur_path = os.path.split(os.path.realpath(__file__))[0]
            cur_path = cur_path + os.sep + ".." + os.sep + 'log' + os.sep + 'edge.log'
            edge_capabilities = DesiredCapabilities.EDGE
            edge_capabilities['edge.usePerProcessProxy'] = True
            edge_capabilities['proxy'] = System.set_proxy(proxy)
            # edge_options = Options()
            return webdriver.Edge(executable_path=self.__get_driver_path("edge"),
                                  capabilities=edge_capabilities, log_path=cur_path, verbose=True)
        else:
            raise ValueError("Edge is not a supported browser with your version of Selenium python library."
                             " Please, upgrade to minimum required version 2.47.0.")

    def __get_driver_path(self, browser):
        default = os.path.split(os.path.realpath(__file__))[0]
        default = default + os.sep + '..' + os.sep + "resource" + os.sep + "driver"
        _browser = browser.lower()
        if _browser == "chrome":
            default = default + os.sep + _browser + os.sep + self.__chromeDriverVersion
            if System.get_os_name() == "linux":
                if System.is64bit():
                    default = default + os.sep + "linux64"
                else:
                    default = default + os.sep + "linux32"
                default = default + os.sep + "chromedriver"
            elif System.get_os_name() == "windows":
                default = default + os.sep + "win32" + os.sep + "chromedriver.exe"

        elif _browser == "edge":
            default = default + os.sep + _browser + os.sep + self.__EdgeDriverVersion \
                      + os.sep + "MicrosoftWebDriver.exe"

        elif _browser == "firefox":
            default = default + os.sep + _browser + os.sep + self.__firefoxDriverVersion
            if System.get_os_name() == "linux":
                if System.is64bit():
                    default = default + os.sep + "linux64"
                else:
                    default = default + os.sep + "linux32"
                default = default + os.sep + "geckodriver"
            elif System.get_os_name() == "windows":
                if System.is64bit():
                    default = default + os.sep + "win64"
                else:
                    default = default + os.sep + "win32"
                default = default + os.sep + "geckodriver.exe"

        elif _browser == "ie":
            default = default + os.sep + _browser + os.sep + self.__ieDriverVersion
            # Use win32 for IE driver only because of performance issue.
            # if (self.__is64bit()):
            #     default = default + os.path.sep + "win64"
            # else:
            #     default = default + os.path.sep + "win32"
            # default = default + os.path.sep + "IEDriverServer.exe"
            default = default + os.sep + "win32" + os.sep + "IEDriverServer.exe"
        return default
