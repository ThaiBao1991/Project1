package utils.cloudflarebypass;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.script.ScriptEngine;
import javax.script.ScriptException;

import org.jsoup.Connection;
import org.jsoup.Connection.Method;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import common.CommonValue;
import common.Enumeration.EnumConfigKey;
import log.CommonLog;
import log.CommonUILog;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import models.LoginInfo;
import models.PageConfig;
import utils.UrlHandler;

/**
 * Using for bypass website protected by cloudflare system
 * 
 * @author mkbyme, Feb 11, 2019
 */
public class CloudFlareByPass {
	private static HashMap<String, CloudFlareByPassResult> _cloudFlareCookies = new HashMap<>();
	private static ScriptEngine _scriptEngine = null;

	private final static String CloudFlareJSChallengeAnswerParam = "jschl_answer";
	private final static String CloudFlareJSChallengeFormId = "challenge-form";
	private final static String CloudFlareCookieName = "cf_clearance";
	private final static int CloudFlareMaximumRetry = 5;

	/**
	 * get javascript engine to excute js challenge
	 * 
	 * @return JavaScriptEngine
	 */
	private static ScriptEngine getScriptEngine() {
		if (_scriptEngine == null) {
			_scriptEngine = new javax.script.ScriptEngineManager().getEngineByName("JavaScript");
		}
		return _scriptEngine;
	}

	/**
	 * Check that html content is protected by CF
	 * 
	 * @param docHtml
	 * @return true - protected
	 */
	private static Boolean checkIsProtected(Document document) {
		Boolean isProtected = false;
		if (document != null) {
			isProtected = document.getElementById(CloudFlareJSChallengeFormId) != null;
		}
		return isProtected;
	}

	/**
	 * Get cloudFlare bypass Cookies
	 * 
	 * @param url
	 * @return String cookies bypass CloudFlare
	 * @author mkbyme, Feb 11, 2019
	 */
	public static String byPassCloudFlareGetText(String url, int retryTime) {
		String ret = "";
		URI uri;
		if (retryTime < CloudFlareMaximumRetry) {
			try {
				uri = new URI(url);
				String host = uri.getHost();
				Boolean isSiteProtectedByCloudFlare = true;
				CloudFlareByPassResult byPassResultCookies = null;
				Document document = null;
				if (_cloudFlareCookies != null && _cloudFlareCookies.containsKey(host)) {
					byPassResultCookies = _cloudFlareCookies.get(host);
				}
				try {

					LoginInfo loginInfo = Config.getLoginInfoByPageCode(host);
					Map<String, String> cookiesMap = new HashMap<>();
					if (loginInfo != null) {
						cookiesMap = UrlHandler.getCookiesMap(loginInfo.getCookies());
					}
					if (byPassResultCookies != null) {
						cookiesMap.put(byPassResultCookies.getCookiesName(), byPassResultCookies.getCookies());
					}

					document = Jsoup.connect(url).userAgent(Constant.USER_AGENT).timeout(CommonValue.getTimeout())
							.cookies(cookiesMap).ignoreHttpErrors(true).get();

					document.outputSettings()
							.charset(SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING));

					isSiteProtectedByCloudFlare = checkIsProtected(document);

				} catch (MalformedURLException e1) {
					System.out.println("Đường dẫn không hợp lệ url = " + url);
					CommonLog.logWarning("Đường dẫn không hợp lệ url = " + url);
				} catch (IOException e) {
					e.printStackTrace();
					CommonLog.logError(e);
				}

				if (isSiteProtectedByCloudFlare) {
					CommonUILog.info("Trang có xác thực bảo vệ CloudFlare, đang xử lý bypass...");
					resolveCloudFlareChallenge(url, document, retryTime);
					return byPassCloudFlareGetText(url, ++retryTime);

				} else if (document != null) {
					ret = document.html();
				} else {
					ret = "";
				}
			} catch (URISyntaxException e) {
				e.printStackTrace();
				CommonLog.logError(e);
			}
		}

		return ret;
	}

	/**
	 * Get cloudFlare bypass Cookies
	 * 
	 * @param url
	 * @return String cookies bypass CloudFlare
	 * @author mkbyme, Feb 11, 2019
	 */
	public static Document byPassCloudFlareGetDocument(String url, int retryTime) {
		String result = byPassCloudFlareGetText(url, retryTime);
		return Jsoup.parse(result);
	}

	/**
	 * Get cloudFlare bypass Cookies
	 * 
	 * @param url
	 * @return String cookies bypass CloudFlare
	 * @author mkbyme, Feb 11, 2019
	 */
	private static CloudFlareByPassResult getCloudFlareByPassCookie(String url) {
		@SuppressWarnings("unused")
		String result = byPassCloudFlareGetText(url, 1);
		return _cloudFlareCookies.get(UrlHandler.getHostFromUrl(url));
	}

	/**
	 * Get cloudFlare bypass Cookies (Map with cookies login)
	 * 
	 * @param url
	 * @return String cookies bypass CloudFlare
	 * @author mkbyme, Feb 11, 2019
	 */
	private static Map<String, String> getCloudFlareByPassCookies(String url, PageConfig pageConfig) {
		LoginInfo loginInfo = Config.getLoginInfoByPageCode(pageConfig.getPageCode());
		Map<String, String> cookiesMap = new HashMap<>();
		if (loginInfo != null) {
			cookiesMap = UrlHandler.getCookiesMap(loginInfo.getCookies());
		}
		if (pageConfig.getByPassCloudFlare()) {
			CloudFlareByPassResult byPassResultCookies = getCloudFlareByPassCookie(url);
			if (byPassResultCookies != null) {
				cookiesMap.put(byPassResultCookies.getCookiesName(), byPassResultCookies.getCookies());
			}
		}

		return cookiesMap;
	}

	/**
	 * Get cloudFlare bypass Cookies (Map with cookies login) in string
	 * 
	 * @param url
	 * @return String cookies bypass CloudFlare
	 * @author mkbyme, Feb 11, 2019
	 */
	public static String getCloudFlareByPassCookiesString(String url, PageConfig pageConfig) {
		StringBuilder sb = new StringBuilder();
		Map<String, String> cookies = getCloudFlareByPassCookies(url, pageConfig);
		cookies.forEach((k, v) -> {
			sb.append(String.format("%s=%s;", k, v));
		});
		return sb.toString();
	}

	/**
	 * Return result passby errorType = OK
	 * 
	 * @param url
	 * @return {@link CloudFlareByPassResult}
	 * @author mkbyme, Feb 11, 2019
	 */
	private static void resolveCloudFlareChallenge(String url, Document document, int retryTime) {
		int domainLen = 0;
		String host = "";
		URL uri;
		String formActionLink = "";
		String byPassRequestUrl = "";
		try {
			uri = new URL(url);
			host = uri.getHost();
			byPassRequestUrl = String.format("%s://%s/", uri.getProtocol(), host);
			domainLen = host.length();
		} catch (MalformedURLException e1) {
			CommonLog.logError(e1);
			e1.printStackTrace();
		}

		// eval challenge javascript result
		String challengeScript = document.selectFirst("script").html();
		String cloudFlareJsFunctionContent = challengeScript.replace("={\"", ".").replace(")};", ");");
		Matcher jschlMatcher = Pattern.compile("([\\+\\-\\*\\/])([^\\w\\;\\}]{20,})[;]")
				.matcher(cloudFlareJsFunctionContent);
		String jschlAnswerScript = "";
		ArrayList<String> lstMathMatcher = new ArrayList<String>();
		double jschlAnswerDouble = 0;
		while (jschlMatcher.find()) {
			String temp = jschlMatcher.group(0);
			if (jschlAnswerDouble == 0) {
				temp = "t = " + temp;
				jschlAnswerDouble++;
			} else {
				temp = "t" + temp;
			}
			lstMathMatcher.add(temp);

		}
		try {
			jschlAnswerScript = String.join(";", lstMathMatcher);
			jschlAnswerDouble = (double) getScriptEngine().eval(jschlAnswerScript);
		} catch (ScriptException e) {
			e.printStackTrace();
		}

		String jschlAnswerStr = String.format(Locale.US, "%.10f", jschlAnswerDouble + domainLen);
		System.out.println(String.format("Compute anwser: %f, Final answer: %s", jschlAnswerDouble, jschlAnswerStr));

		// send request
		Map<String, String> params = new HashMap<>();
		Element challengeForm = document.getElementById(CloudFlareJSChallengeFormId);
		if (challengeForm != null) {
			formActionLink = challengeForm.attr("action");
			params = buildFormData(challengeForm, jschlAnswerStr);

		} else {
			CommonLog.logWarning("Không tìm thấy form challenge-form để by pass cloudflare");
		}

		if (formActionLink.startsWith("/")) {
			formActionLink = formActionLink.substring(1);
		}
		byPassRequestUrl += formActionLink;

		try {
			System.out.println("Request server: " + byPassRequestUrl);
			for (int i = 0; i < 5; i++) {
				Thread.sleep(1000);
				System.out.println("Wating...");

				CommonUILog.info(String.format("Đang chờ gửi request by pass %d(s)...", (i + 1)));
			}

			Connection.Response res = Jsoup.connect(byPassRequestUrl).data(params).method(Method.GET)
					.userAgent(Constant.USER_AGENT).timeout(CommonValue.getTimeout()).ignoreHttpErrors(true).execute();

			document = res.parse();

			// Save cookies
			String cf_clearance = res.cookie(CloudFlareCookieName);
			if (cf_clearance != null && !cf_clearance.isEmpty()) {
				CloudFlareByPassResult byPassResult = new CloudFlareByPassResult();
				byPassResult.setCookiesWithName(CloudFlareCookieName, cf_clearance);
				_cloudFlareCookies.put(host, byPassResult);
				System.out.println(res.cookies());

				CommonUILog.info("Xử lý bypass thành công token = " + cf_clearance);
			} else {
				CommonUILog.info(String.format("Xử lý bypass thất bại lần %d, thử lại...", retryTime));
			}

		} catch (IOException | InterruptedException e) {
			e.printStackTrace();
		}

	}

	/**
	 * Build form content to post cloudflare resolve
	 * 
	 * @param form
	 *            cloudFlare Form
	 * @param jschlAnswerStr
	 *            anwser string
	 * @return Hash
	 */
	private static Map<String, String> buildFormData(Element form, String jschlAnswerStr) {
		Map<String, String> params = new HashMap<>();
		if (form != null) {
			Elements inputs = form.select("[name]");
			if (inputs != null && inputs.size() > 0) {
				inputs.forEach(i -> {
					String name = i.attr("name");
					String value = i.val();
					if (name != null && !name.isEmpty() && !params.containsKey(name)) {
						if (CloudFlareJSChallengeAnswerParam.equalsIgnoreCase(name)) {
							params.put(CloudFlareJSChallengeAnswerParam, jschlAnswerStr);
						} else {
							params.put(name, value);
						}
					}
				});
			}
		}
		return params;
	}

}
