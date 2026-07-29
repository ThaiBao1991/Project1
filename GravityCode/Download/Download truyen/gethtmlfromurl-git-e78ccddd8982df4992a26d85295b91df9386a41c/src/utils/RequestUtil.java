package utils;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;

import common.CommonValue;
import common.Enumeration.EnumConfigKey;
import log.CommonLog;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import models.LoginInfo;
import models.PageConfig;
import utils.cloudflarebypass.CloudFlareByPass;

/**
 * Request with common info(login data, user-agent...)
 * 
 * @author nxcuo
 *
 */
public class RequestUtil {

	private final static String Post = "POST";
	private final static String Get = "GET";

	/**
	 * Get data from url with pageConfig info
	 * 
	 * @param url
	 * @param pageConfig
	 * @return Document
	 * @author mkbyme, Jul 29, 2019
	 */
	public static Document get(String url, PageConfig pageConfig) {
		Document doc = null;
		if (pageConfig.getByPassCloudFlare()) {
			doc = CloudFlareByPass.byPassCloudFlareGetDocument(url, 1);
		} else {

			LoginInfo loginInfo = Config.getLoginInfoByPageCode(pageConfig.getPageCode());
			Map<String, String> cookiesMap = new HashMap<>();
			if (loginInfo != null) {
				cookiesMap = UrlHandler.getCookiesMap(loginInfo.getCookies());
			}
			try {
				doc = Jsoup.connect(url).userAgent(Constant.USER_AGENT).timeout(CommonValue.getTimeout())
						.ignoreHttpErrors(true).followRedirects(true).cookies(cookiesMap).get();
			} catch (IOException e) {
				CommonLog.logError(e);
				e.printStackTrace();
			}
		}

		return doc;

	}

	/*
	 * get content ajax
	 */
	public static String postFormData(String url, String formData, HashMap<String, String> requestHeaders,
			PageConfig pageConfig) throws IOException {
		byte[] postData = formData.getBytes(StandardCharsets.UTF_8);
		String cookies = CloudFlareByPass.getCloudFlareByPassCookiesString(url, pageConfig);
		URL u = new URL(url);
		HttpURLConnection conn = (HttpURLConnection) u.openConnection();
		conn.setDoOutput(true);
		conn.setInstanceFollowRedirects(false);
		conn.setRequestMethod(Post);
		conn.setRequestProperty("User-Agent", Constant.USER_AGENT);
		conn.setRequestProperty("Cookie", cookies);
		int timeout = CommonValue.getTimeout();
		conn.setConnectTimeout(timeout);
		conn.setReadTimeout(timeout);
		if (requestHeaders != null) {
			for (String key : requestHeaders.keySet()) {
				conn.setRequestProperty(key, requestHeaders.get(key));
			}
		}

		conn.setUseCaches(false);
		if (postData.length > 0) {
			try (DataOutputStream wr = new DataOutputStream(conn.getOutputStream())) {
				wr.write(postData);
			}
		}

		conn.connect();

		BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(),
				SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING)));
		String tempReader = "";
		StringBuilder sb = new StringBuilder();
		// get respond content.
		while ((tempReader = br.readLine()) != null) {
			sb.append(tempReader);
			sb.append("\r\n");
		}

		br.close();
		conn.disconnect();

		return sb.toString();

	}

	/*
	 * get content ajax
	 */
	public static String getData(String url, HashMap<String, String> requestHeaders, PageConfig pageConfig)
			throws IOException {
		String cookies = CloudFlareByPass.getCloudFlareByPassCookiesString(url, pageConfig);
		URL u = new URL(url);
		HttpURLConnection conn = (HttpURLConnection) u.openConnection();
		conn.setInstanceFollowRedirects(false);
		conn.setRequestMethod(Get);
		conn.setRequestProperty("User-Agent", Constant.USER_AGENT);
		conn.setRequestProperty("Cookie", cookies);
		int timeout = CommonValue.getTimeout();
		conn.setConnectTimeout(timeout);
		conn.setReadTimeout(timeout);
		if (requestHeaders != null) {
			for (String key : requestHeaders.keySet()) {
				conn.setRequestProperty(key, requestHeaders.get(key));
			}
		}

		conn.setUseCaches(false);

		conn.connect();

		BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(),
				SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING)));
		String tempReader = "";
		StringBuilder sb = new StringBuilder();
		// get respond content.
		while ((tempReader = br.readLine()) != null) {
			sb.append(tempReader);
			sb.append("\r\n");
		}

		br.close();
		conn.disconnect();

		return sb.toString();

	}
}
