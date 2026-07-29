package utils;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.PatternSyntaxException;

public class UrlHandler {
	/**
	 * @param eval
	 *            (math String)
	 * @return 0 if not fine.
	 */
	public static int eval(String eval) {
		String arr[];
		if (eval.contains("-")) {
			arr = eval.split("-");
			return Integer.parseInt(arr[0]) - Integer.parseInt(arr[1]);
		} else if (eval.contains("+")) {
			arr = eval.split("+");
			return Integer.parseInt(arr[0]) + Integer.parseInt(arr[1]);
		} else {
			return Integer.parseInt(eval);
		}

	}

	public static String getHostFromPattern(String cssQuery, String storyUrl) {
		// if has ; signal -> do this
		if (cssQuery.contains(";")) {

			String hostPattern = cssQuery.split("\\;")[1];
			if (hostPattern.toUpperCase().contains("R")) {
				String arrHostPatternAndValue[] = hostPattern.split("\\&");
				if (arrHostPatternAndValue.length > 1) {
					String regex = arrHostPatternAndValue[0].split("\\=")[1];
					String replacement = "";
					if (arrHostPatternAndValue.length > 2) {
						replacement = arrHostPatternAndValue[1].split("\\=")[1];
					}

					return storyUrl.replaceAll(regex, replacement);
				}
			}
		}

		return cssQuery;
	}

	/**
	 * Use for page pattern replacement
	 * 
	 * @param pagePattern
	 * @param storyUrl
	 * @param replacement
	 * @return
	 */
	public static String getPagePatternUrl(String pagePattern, String storyUrl, String replacement) {
		if (pagePattern.contains(";")) {
			String pattern = getHostFromPattern(pagePattern, storyUrl);
			pattern += replacement;
			return pattern;
		} else {
			return normalizeHostAndPath(storyUrl, replacement);
		}
	}

	public static String normalizeHost(String host) {
		if (host.startsWith("//")) {
			host = host.substring(2);
		}
		if (!host.startsWith("http")) {
			host = "http://" + host;
		}
		if (host.endsWith("/")) {
			return host.substring(0, host.length() - 1);
		}
		return host.trim();
	}

	/**
	 * Nomalize with http or https prefix
	 * 
	 * @param host
	 *            hostname
	 * @param demoLink
	 *            link demo to get http prefix
	 * @return
	 */
	public static String normalizeHost(String host, String demoLink) {
		if (host.startsWith("//")) {
			host = host.substring(2);
		}
		if (!host.startsWith("http")) {
			if (demoLink != null && !demoLink.isEmpty() && demoLink.startsWith("http")) {
				String prefix = demoLink.substring(0, demoLink.indexOf("//") + 2);
				host = prefix + host;
			} else {

				host = "http://" + host;
			}
		}
		if (host.endsWith("/")) {
			return host.substring(0, host.length() - 1);
		}
		return host;
	}

	public static String normalizeHostAndPath(String host, String path) {
		return normalizeHost(host) + normalizePath(path);
	}

	public static String normalizeHostAndPath(String host, String path, String demoLink) {
		return normalizeHost(host, demoLink) + normalizePath(path);
	}

	public static String normalizePath(String path) {
		if (path.startsWith("/")) {
			return path;
		}
		return "/" + path.trim();
	}

	/**
	 * Convert string cookies into map, using for jsoup
	 * 
	 * @param cookiesString
	 * @return Map Cookie
	 */
	public static Map<String, String> getCookiesMap(String cookiesString) {
		Map<String, String> ret = new HashMap<>();
		if (cookiesString != null && !cookiesString.isEmpty()) {

			try {
				String[] arr = cookiesString.split(";");
				for (String string : arr) {
					String[] keyValue = string.split("=");
					if (keyValue.length > 1 && keyValue[1] != null) {
						ret.put(keyValue[0], keyValue[1]);
					}
				}
			} catch (PatternSyntaxException | IndexOutOfBoundsException | NullPointerException e) {
				e.printStackTrace();
			}

		}
		return ret;

	}

	/**
	 * Get host from URL
	 * 
	 * @param url
	 * @return
	 */
	public static String getHostFromUrl(String url) {
		String ret = "";
		URL uri;
		try {
			uri = new URL(url);
			ret = uri.getHost();
		} catch (MalformedURLException e) {
			e.printStackTrace();
		}
		return ret;

	}

}
