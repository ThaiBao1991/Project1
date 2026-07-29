package mkgethtml;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;

import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLHandshakeException;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import common.CommonValue;
import common.Enumeration;
import common.Enumeration.EnumConfigKey;
import log.CommonLog;
import mk.constant.Constant;
import mk.function.FuncParamStringBuilder;
import models.Chapter;
import models.LoginInfo;
import models.PageConfig;
import resource.text.Messages;
import utils.InstallCert;
import utils.IpHandler;
import utils.RequestUtil;
import utils.UrlHandler;
import utils.cloudflarebypass.CloudFlareByPass;

/**
 * @author Adminz
 *
 */
/**
 * @author Adminz
 *
 */
/**
 * @author Adminz
 *
 */
public class GetHtmlCss {

	/**
	 * give us know when is the last page of urlsite
	 *
	 * @param listTagAUrl
	 *            - HTML Element get all link of chapter on page
	 * @param urlFisrtPage
	 *            - some website will redirect to the firstpage when we over
	 *            size paging
	 * @param urlLastPage
	 *            - some website will redirect to the lastpage when we over size
	 *            paging
	 * @param p
	 *            - PageConfig store all we need to know THAT SITE will use
	 *            URLFIRSTPAGE or URLLASTPAGE or EMPTY_PAGE see more in
	 *            MkEnum.OverPageCountState
	 * @return true if we over load paging size.
	 */
	public static Boolean checkPageFound(Element listTagAUrl, String firstChapterLink, String lastChapterLink,
			PageConfig p) {
		int size = listTagAUrl.select("a").size();
		String chapterLinkToCompare = "";

		// with page doesn't support this
		if (p.getOverMaxSizePageCountState() == Enumeration.OverMaxSizePageCountState.MOVE_TO_PAGE_WITHOUT_CHAPTER_LIST) {

			return size < 1;
		}

		// page support redirect when error(overload page count)
		if (p.getOverMaxSizePageCountState() == Enumeration.OverMaxSizePageCountState.MOVE_TO_LAST) {
			chapterLinkToCompare = listTagAUrl.select("a").eq(size - 1).attr("href").toString();
			return chapterLinkToCompare.equalsIgnoreCase(lastChapterLink);

		} else {
			chapterLinkToCompare = listTagAUrl.select("a").eq(0).attr("href").toString();
			return chapterLinkToCompare.equalsIgnoreCase(firstChapterLink);
		}
	}

	/**
	 * remove all unneeded content from html page by htmlTAG or string
	 * 
	 * @param doc
	 *            {@link Document} Document want to remove
	 * @param cssRemoveContent
	 *            {@link String} contains htmlTAG,cssSelector, string content
	 * @return a {@link Document} after remove
	 * @author mkbyme Jun 30, 2017
	 */
	public static Document filterHtml(Document doc, String cssRemoveContent) {
		String[] listFilter;
		try {
			listFilter = cssRemoveContent.split(";");
			for (String str : listFilter) {
				if (!str.isEmpty()) {
					if (isHtmlAttr(str)) {
						String attrName = str.substring(str.indexOf("[") + 1, str.length() - 1);
						doc.select(str).removeAttr(attrName);
					} else {
						doc.select(str).remove();
					}
				}
			}
		} catch (Exception e1) {
			System.out.println(e1.getMessage());
			CommonLog.logError(e1);
		}
		return doc;

	}

	/**
	 * 
	 * @param e
	 * @param cssRemoveContent
	 * @return
	 * @author mkbyme Jun 30, 2017
	 */
	public static Elements filterHtml(Elements e, String cssRemoveContent) {
		if (cssRemoveContent != null) {
			String strContentFilter = "", strRemoveContentX = cssRemoveContent;
			int iStart = cssRemoveContent.indexOf('"');
			int iEnd = cssRemoveContent.lastIndexOf('"');
			if (iStart > -1 && iEnd > -1) {
				strContentFilter = cssRemoveContent.substring(iStart + 1, iEnd);
				strRemoveContentX = cssRemoveContent.substring(0, iStart - 1) + cssRemoveContent.substring(iEnd + 1);
			}
			// remove unwanted content
			String[] listFilter;
			try {
				listFilter = strRemoveContentX.split(";");
				for (String str : listFilter) {
					if (!str.isEmpty()) {
						if (isHtmlAttr(str)) {
							String attrName = str.substring(str.indexOf("[") + 1, str.length() - 1);
							e.select(str).removeAttr(attrName);
						} else {
							e.select(str).remove();
						}
					}
				}
				if (!strContentFilter.isEmpty()) {
					String[] listFilterStr = strContentFilter.split(",");

					String sb = e.html();
					for (String str : listFilterStr) {
						sb = sb.replace(str, "");
					}
					e.html(sb.toString());
				}

			} catch (Exception e1) {
				System.out.println(e1.getMessage());
				CommonLog.logError(e1);
			}
		}
		return e;
	}

	/**
	 * give a Chapter obj contain title and content of chapter story
	 *
	 * @param chapterUrl
	 *            - should check normalize Path if PageConfig is not absoluted
	 *            link
	 * @param pageConfig
	 *            - pageConfig
	 * @return models.Chapter
	 * @throws IOException
	 */
	public static Chapter getChapterTitleAndContent(int id, String chapterUrl, PageConfig pageConfig)
			throws IOException {

		String cssChapterTitle = pageConfig.getCssQueryGetChapterTitle();
		String cssChapterContent = pageConfig.getCssQueryGetChapterContent();
		String cssRemoveContent = pageConfig.getCssFilter();
		Boolean isEnableChapterSign = pageConfig.getIsEnableChapterSign();

		Chapter chapter = null;
		Boolean isAjax = false;
		chapter = getChapterTitleAndContentAjax(id, chapterUrl, pageConfig);
		if (chapter != null) {
			isAjax = true;
		} else {
			chapter = new Chapter();
		}

		if (!isAjax) {

			Document htmlPage = null;

			String html = getHtmlStringFromURLbyCharset(chapterUrl, pageConfig);
			if (html.isEmpty()) {
				if (chapterUrl.startsWith("http") || chapterUrl.startsWith("https") || chapterUrl.startsWith("www")) {
					chapter.isGetFailed = true;
				}
				return chapter;
			}

			htmlPage = Jsoup.parse(html, SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING));

			// check and checkVip content
			VipContentLeech.leechVipContent(htmlPage, chapterUrl, pageConfig);
			Boolean isHasCapcha = checkIsHasGoogleCapchaBlock(htmlPage, chapterUrl);

			// not has capcha then download
			if (!isHasCapcha) {
				Elements content = htmlPage.select(cssChapterContent);
				if (content == null) {
					chapter.isGetFailed = true;
					return chapter;
				}

				// chapter title
				if (isEnableChapterSign) {
					if (htmlPage.select(cssChapterTitle).size() == 0) {
						chapter.setTitle(CommonValue.getChapterNameWithSignal(id + 1, ""));
					} else {
						chapter.setTitle(CommonValue.getChapterNameWithSignal(id + 1,
								htmlPage.select(cssChapterTitle).first().text().trim()));
					}
				} else if (!cssChapterTitle.isEmpty() && !htmlPage.select(cssChapterTitle).isEmpty()) {
					chapter.setTitle(htmlPage.select(cssChapterTitle).first().text().trim());
				} else {
					chapter.setTitle("");
				}

				htmlPage.children().stream().close();

				Boolean hasImage = injectChapterHasImageLink(content, null);

				// remove unwanted content
				filterHtml(content, cssRemoveContent);

				chapter.setContent(CommonValue.getIDandTitleString(id, chapter.getTitle(), content.html(), hasImage));

			} else {
				chapter.setIsHasCapchaBlock(isHasCapcha);
			}
		}
		return chapter;
	}

	/**
	 * give a Chapter obj contain title and content of chapter story
	 *
	 * @param chapterUrl
	 *            - should check normalize Path if PageConfig is not absoluted
	 *            link
	 * @param pageConfig
	 * @return models.Chapter
	 * @throws IOException
	 */
	public static Chapter getChapterTitleAndContentAjax(int id, String chapterUrl, PageConfig pageConfig) {
		Chapter c = null;
		if (pageConfig.getIsForumType()) {
			// forum type
			c = GetHtmlCsMix.getChapterTitleAndContentOfForum(id, chapterUrl, pageConfig);
		} else {
			switch (pageConfig.getPageCode()) {
			case "sstruyen.com":
				c = GetHtmlCsMix.getChapterTitleAndContentSSTruyen(id, chapterUrl, pageConfig);
				break;
			case "tangthucac.com":
				c = GetHtmlCsMix.getChapterTitleTangThuCacDotCom(id + 1, chapterUrl, pageConfig);
				break;
			case "truyendich.org":
				c = GetHtmlCsMix.getChapterTitleTruyenDichDotOrg(id, chapterUrl, pageConfig);
				break;
			}

		}
		return c;
	}

	/**
	 * @param content
	 *            - elent content img tag to show content
	 * @return true - if content has img tag
	 * @author mkbyme Jan 27, 2019
	 */
	public static Boolean injectChapterHasImageLink(Elements content,
			FuncParamStringBuilder funcCustomStringBuilderBeforeParseToElement) {
		Boolean hasImage = false;
		Elements imgs = null;
		if (content != null && SettingOption.getBoolean(EnumConfigKey.IS_SHOW_PAGE_HAS_IMAGE, false)) {
			// get list img
			imgs = content.select("img");
			hasImage = imgs.size() > 0;
			StringBuilder sb = new StringBuilder();
			int startPos = 0, lastPos = -1;

			sb.append(content.html());

			for (int i = 0; i < imgs.size(); i++) {
				lastPos = sb.indexOf("<img", startPos);
				String strInsert = String.format(Messages.getGlobalString("log.viewImageOfChapter"),
						imgs.get(i).attr("src").toString(), (i + 1));
				if (lastPos > -1) {
					sb.insert(lastPos, strInsert);
				}

				startPos = lastPos + strInsert.length() + 10;
			}

			if (funcCustomStringBuilderBeforeParseToElement != null) {
				// custom stringbuilder before push back to Element
				try {
					sb = funcCustomStringBuilderBeforeParseToElement.call(sb);
				} catch (Exception e) {
					CommonLog.logError(e);
					e.printStackTrace();
				}
			}
			// cast content modifired to Node
			content.html(sb.toString());
		}
		return hasImage;
	}

	/**
	 * custom content before parse to keep formatting in some page using text
	 * format
	 * 
	 * @param html
	 *            - html String
	 * @param url
	 *            - url get content
	 * @return
	 */
	public static StringBuilder customHtmlStringBeforeParse(StringBuilder html, String url) {
		if (url.contains("truyen.tangthuvien")) {
			int start = 0, end = 0;
			start = html.indexOf("box-chap");
			if (start > 0) {
				start += 10;
				end = html.indexOf("</div>", start);
			}
			if (start > 0 && end > 0) {
				String content = html.subSequence(start, end).toString();

				content = content.replaceAll("\\r|\\n", "<br>");

				html.replace(start, end, "");
				html.insert(start, content);
			}
		}
		return html;
	}

	/**
	 * @param url
	 *            - link of chapter want to get with encoding from Config
	 * @param isUseJsoupGet
	 * @return string of html site
	 * @throws IOException
	 */
	public static String getHtmlStringFromURLbyCharset(String url, PageConfig pageConfig) {
		String back = "";

		try {
			if (pageConfig.getByPassCloudFlare()) {
				back = CloudFlareByPass.byPassCloudFlareGetText(url, 1);
			} else {

				Boolean isUseJsoupGet = pageConfig.getIsUseJsoupGet();
				URL u = new URL(url);

				if (isUseJsoupGet) {
					Document docHTML = RequestUtil.get(url, pageConfig);
					docHTML.outputSettings()
							.charset(SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING));
					back = docHTML.html();
				} else {

					InputStream is = null;
					HttpURLConnection conn = null;
					int respondCode = 0;

					conn = (HttpURLConnection) u.openConnection();
					conn.setRequestProperty("User-Agent", Constant.USER_AGENT);
					conn.setRequestProperty("Content-Type", "text/html; charset=utf-8");
					// setup request
					conn.setConnectTimeout(CommonValue.getTimeout());
					conn.setReadTimeout(CommonValue.getTimeout());
					// gen a random ip to passing
					if (url.contains("truyencv")) {
						conn.setRequestProperty("X-Forwarded-For", IpHandler.getNewIPAddress());
					}
					// gen a random ip to passing
					if (url.contains("wikidich")) {
						conn.setRequestProperty("Host", "wikidich.com");
					}
					// get cookies
					LoginInfo loginInfo = Config.getLoginInfoByPageCode(u.getHost());
					// set cookies
					if (loginInfo != null) {
						conn.setRequestProperty("Cookie", loginInfo.getCookies());
					}

					conn.connect();
					respondCode = conn.getResponseCode();

					if (respondCode == 301) {
						String redirect = conn.getHeaderField("Location");
						conn.disconnect();
						if (redirect.startsWith("https://")) {
							conn = (HttpsURLConnection) new URL(redirect).openConnection();
						} else {
							conn = (HttpURLConnection) new URL(redirect).openConnection();
						}
						// setup request
						conn.setConnectTimeout(CommonValue.getTimeout());
						conn.setReadTimeout(CommonValue.getTimeout());
						conn.setRequestProperty("User-Agent", Constant.USER_AGENT);
						// gen a random ip to passing
						if (url.contains("truyencv")) {
							conn.setRequestProperty("X-Forwarded-For", IpHandler.getNewIPAddress());
						}
						// gen a random ip to passing
						if (url.contains("wikidich")) {
							conn.setRequestProperty("Host", "wikidich.com");
						}
					}
					is = conn.getInputStream();

					BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"));// Config.get(EnumConfigKey.ENCODING).toString()));
					String tempReader = "";
					StringBuilder sb = new StringBuilder();
					// get respond content.
					while ((tempReader = br.readLine()) != null) {
						sb.append(tempReader);
						sb.append("\n");
					}

					br.close();

					if (conn != null) {
						conn.disconnect();
					}
					sb = customHtmlStringBeforeParse(sb, url);
					back = sb.toString();
				}
			}
		} catch (MalformedURLException e) {
			CommonLog.logWarning("Link không hợp lệ: " + url);
		} catch (Exception e) {
			CommonLog.logError(e);
			e.printStackTrace();
		}
		return back;
	}

	/**
	 * provide to get number of chapter on 1 page of site
	 *
	 * @param listTagAUrl
	 *            - HTML Element get all link of chapter on page
	 * @param cssQuerryGetListChapterUrl
	 *            - select div or container store list chapter
	 * @return an Array of String contain all chapter's URL on 1 page.
	 * @throws IOException
	 */
	public static ArrayList<String> getListChaptersOnPage(Element listTagAUrl) throws IOException {
		ArrayList<String> listChapter = new ArrayList<>();
		listTagAUrl.select("a").forEach((a) -> {
			String link = a.attr("href").toString();
			if (!listChapter.contains(link)) {
				listChapter.add(link);
			}
		});

		return listChapter;
	}

	/**
	 * Use for querySelectorAll(only)
	 * 
	 * @param el
	 *            - Elemenst (list Element form querySelectorAll)
	 * @param cssQueryListChapter
	 * @param specialList
	 *            - arrList(start, end)
	 * @return - Element listTagAUrl
	 */
	public static Element getListTagAUrlSpecialCssQuery(Document doc, String cssQueryListChapter,
			ArrayList<String> specialList) {

		ArrayList<Element> list = doc.select(cssQueryListChapter).select("a");
		int start, end;
		try {
			start = Integer.parseInt(specialList.get(0));
			end = UrlHandler.eval(specialList.get(1).replace("n", String.valueOf(list.size())));
		} catch (Exception e) {
			start = 0;
			end = list.size();
		}

		Element listTagAUrl = doc.createElement("div");
		for (int i = start; i < end; i++) {
			listTagAUrl.appendChild(list.get(i));
		}

		return listTagAUrl;
	}

	public static String getRespondLocation(String url) throws IOException, SSLHandshakeException {

		URL u;
		HttpURLConnection huc;
		u = new URL(url);

		huc = (HttpURLConnection) u.openConnection();
		huc.setConnectTimeout(5000);
		huc.setRequestMethod("GET");
		try {
			huc.connect();
		} catch (SSLHandshakeException e) {
			try {
				InstallCert.main(new String[] { u.getHost() });
				huc.connect();
				throw new Exception();
			} catch (Exception e1) {
				throw new SSLHandshakeException(e.getMessage());
			}
		} catch (IOException e) {
			CommonLog.logError(e);
			e.printStackTrace();
		}

		return huc.getURL().toString();
	}

	/**
	 * Use for querySelectorAll(only)
	 * 
	 * @param cssQueryListChapter
	 *            -
	 * @param specString
	 *            - special to detemine range of list {start=0&end=n}
	 * @return arrList - {arr[0] is start value, arr[1] is end value}
	 */
	public static ArrayList<String> getSpecialStringFromQuery(String cssQueryListChapter) {

		String specString = cssQueryListChapter.split("[\\{\\}]")[1];

		String[] arrSpecString = specString.split("&");
		ArrayList<String> arrListSpec = new ArrayList<>();
		// remove empty entries
		for (int i = 0; i < arrSpecString.length; i++) {
			if (!arrSpecString[i].isEmpty()) {
				String[] arrTemp = arrSpecString[i].split("=");
				arrListSpec.add(arrTemp[1].toLowerCase());
			}
		}
		if (arrListSpec.size() < 1) {
			arrListSpec.add("0");
			arrListSpec.add("n");
		}

		return arrListSpec;
	}

	/**
	 * Check html Tag is tag or attribute
	 * 
	 * @param tagToCheck
	 * @return {@link Boolean} true if it is attribute
	 */
	public static Boolean isHtmlAttr(String tagToCheck) {
		return tagToCheck.trim().startsWith("[");
	}

	/**
	 * dectect that document are downloading has google capcha or not
	 * 
	 * @param document
	 * @return true if has
	 * @author mkbyme Jul 1, 2017
	 */
	private static Boolean checkIsHasGoogleCapchaBlock(Document document, String hostName) {
		Boolean bIsHasCapcha = false;
		if (document != null && hostName.contains("truyencv")) {

			Elements e = document.select("body");
			if (e != null) {
				String sHtmlContent = e.html();
				if (sHtmlContent.indexOf("recaptcha") > 0) {
					bIsHasCapcha = true;
				}
			}
		}

		return bIsHasCapcha;
	}

	public static Boolean hasImageInPage(Elements content) {
		Boolean hasImage = false;
		if (content != null) {
			hasImage = content.select("img").size() > 0;

		}
		return hasImage;
	}

}
