package utils;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

import mk.constant.Constant;

public class GetFileUtil {
	public static String getStringContentFromURI(String url) {
		URL u;
		BufferedReader br;
		try {
			u = new URL(url);
			HttpURLConnection conn = (HttpURLConnection) u.openConnection();
			conn.setDoOutput(true);
			conn.connect();

			br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
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
		} catch (IOException e) {

		}
		return "";
	}

	/**
	 * getFileContent
	 * 
	 * @param url
	 *            - url of file
	 * @param timeOut
	 *            - timeOut of request
	 * @return file in string
	 */
	public static String getStringContentFromURI(String url, int timeOut) {
		URL u;
		BufferedReader br;
		try {
			u = new URL(url);
			HttpURLConnection conn = (HttpURLConnection) u.openConnection();
			conn.setDoOutput(true);
			conn.setRequestProperty("User-Agent", Constant.USER_AGENT);
			conn.setConnectTimeout(timeOut);
			conn.connect();

			br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
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
		} catch (IOException e) {

		}
		return "";
	}
}
