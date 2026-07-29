/**
 * 
 */
package mkgethtml.vipcontentleech;

import java.net.URL;

import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import com.google.gson.Gson;

import log.CommonLog;
import models.LoginInfo;
import models.PageConfig;
import utils.RequestUtil;
import utils.UrlHandler;

/**
 * @author nxcuo Class process leech vip content on host TruyenYY.Com
 */
public class TruyenYYVipContentLeech implements IVipContentLeech {

	/**
	 * leechVip on truyenyy.com
	 * 
	 * @see mkgethtml.vipcontentleech.IVipContentLeech#leechVipContent(org.jsoup.nodes.Document,
	 *      java.net.URL, models.LoginInfo, java.lang.String, java.lang.String,
	 *      java.lang.Boolean, java.lang.Boolean)
	 * @since 2020.03.21 - fix content layout change
	 */
	@Override
	public void leechVipContent(Document document, URL url, LoginInfo loginInfo, PageConfig pageConfig) {
		try {

			String cssChapterContent = pageConfig.getCssQueryGetChapterContent();
			Element hasVipContent = document.getElementById("vip-content-placeholder");
			if (hasVipContent != null) {
				Elements listContent = document.select(cssChapterContent);

				// remove duplicate content when has vip content
				if (listContent != null) {
					int size = listContent.size();
					while (size > 1) {
						Element e = listContent.get(--size);
						if (e != null) {
							e.remove();
						}
					}
				}

				String chapterId = document.select("#id_chap_content script").first().html();
				int beginIndex = -1, endIndex = -1;
				beginIndex = chapterId.indexOf("$.get(\"");
				endIndex = chapterId.indexOf("\")", beginIndex);
				beginIndex += "$.get(\"".length();
				String chapterAjaxURLContent = chapterId.substring(beginIndex, endIndex).replace("&part=0", "");

				if (!chapterAjaxURLContent.isEmpty()) {
					String requestUrl = UrlHandler.normalizeHostAndPath(url.getHost(), chapterAjaxURLContent,
							pageConfig.getUrlPageTest());
					requestUrl = requestUrl.replace("http", "https");

					String result = RequestUtil.getData(requestUrl, null, pageConfig);
					if (result != null && !result.isEmpty()) {
						result = removeRandomStyleString(result);
						hasVipContent.html(result);
					}
				}
			}
		} catch (IndexOutOfBoundsException e) {
			CommonLog.logError(e);
			e.printStackTrace();
		}

		catch (Exception e) {
			CommonLog.logError(e);
			e.printStackTrace();
		}

	}

	/**
	 * remove protect content string from host truyenyy.com
	 * 
	 */
	private String removeRandomStyleString(String data) {
		int start = -1, end = -1, temp = 0;

		// remove json struct
		Gson gson = new Gson();
		TruyenYYContent content = gson.fromJson(data, TruyenYYContent.class);
		StringBuilder sb = null;
		// get content
		int length = content.content.length();
		if (length > 0) {
			start = content.content.indexOf("<body>");
			start += "<body>".length();
			end = content.content.lastIndexOf("</body>");
			sb = new StringBuilder(content.content.substring(start, end));
			start = end = -1;
		}
		String findStyle = "<style>";
		String findCloseStype = "</style>";
		int findCloseStyleLength = findCloseStype.length();

		start = sb.indexOf(findStyle, temp);
		end = sb.indexOf(findCloseStype, start + 1);

		// remove style mix
		while (end > -1) {
			if (start > -1) {
				sb.replace(start, end + findCloseStyleLength, "");
			}

			start = sb.indexOf(findStyle, start + 1);
			if (start > 0) {
				end = sb.indexOf(findCloseStype, start + 1);
			} else {
				end = -1;
			}
		}

		findStyle = "style=";
		findCloseStype = "</";

		start = sb.indexOf(findStyle, 0);
		end = sb.indexOf(findCloseStype, start);
		start = getOpenFromStyleEqual(sb, start);
		end = getCloseFromStyleEqual(sb, end);
		temp = 0;
		while (end > -1) {
			if (start > -1) {
				sb.replace(start, end + 1, "");
			}

			start = sb.indexOf(findStyle, start + 1);
			if (start > 0) {
				end = sb.indexOf(findCloseStype, start + 1);
				start = getOpenFromStyleEqual(sb, start);
				end = getCloseFromStyleEqual(sb, end);
			} else {
				end = -1;
			}
		}
		String dataX = sb.toString().replaceAll("(<\\w{3,10}>)|(<\\/\\w{3,10}>)", "");
		return dataX;
	}

	/**
	 * Get open slash from string mix style=
	 * 
	 * @param sb
	 * @param indexOfStyleEqual
	 * @return
	 */
	private int getOpenFromStyleEqual(StringBuilder sb, int indexOfStyleEqual) {
		indexOfStyleEqual -= 3;
		for (int i = 0; i < 100; i++) {
			if (indexOfStyleEqual < 0) {
				break;
			}
			if (sb.charAt(indexOfStyleEqual) == '<') {
				break;
			}
			indexOfStyleEqual--;

		}
		return indexOfStyleEqual;

	}

	/**
	 * Get close slash from string mix style=
	 * 
	 * @param sb
	 * @param indexOfStyleEqual
	 * @return
	 */
	private int getCloseFromStyleEqual(StringBuilder sb, int indexOfStyleEqual) {
		int length = sb.length();
		indexOfStyleEqual += 3;
		for (int i = 0; i < 100; i++) {
			if (indexOfStyleEqual > length) {
				break;
			}
			if (sb.charAt(indexOfStyleEqual) == '>') {
				break;
			}
			indexOfStyleEqual++;

		}

		return indexOfStyleEqual;

	}

	/**
	 * JSON from API get vip content truyenyy
	 * 
	 * @author nxcuo
	 *
	 */
	public class TruyenYYContent {
		public Boolean ok;
		public String content;

		public TruyenYYContent() {

		}
	}
}
