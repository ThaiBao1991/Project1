package mkgethtml;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.swing.JLabel;
import javax.swing.JTextArea;

import org.json.JSONObject;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import common.CommonExceptionHandle;
import common.CommonValue;
import common.Enumeration.EnumConfigKey;
import log.CommonLog;
import log.CommonUILog;
import mk.constant.Constant;
import models.Chapter;
import models.PageConfig;
import resource.text.Messages;
import utils.RequestUtil;
import utils.UrlHandler;

public class GetHtmlCsMix {

	/**
	 * Use for get content on Forum site
	 * 
	 * @param isEnableChapterSign
	 * @param cssRemoveContent
	 * @param cssChapterContent
	 * @param cssChapterTitle
	 * 
	 * @return {@link Chapter}
	 */
	public static Chapter getChapterTitleAndContentOfForum(int id, String chapterUrl, PageConfig pageConfig) {
		String cssChapterContent = pageConfig.getCssQueryGetChapterContent();
		String cssRemoveContent = pageConfig.getCssFilter();
		Chapter back = new Chapter();
		Document htmlPage = null;
		try {
			htmlPage = RequestUtil.get(chapterUrl, pageConfig);
			htmlPage.children().stream().close();
		} catch (Exception e) {
			CommonLog.logError(e);
			return back;
		}

		Elements content = htmlPage.select(cssChapterContent);

		if (content == null) {
			return back;
		}

		StringBuilder sb = new StringBuilder();

		// gen chapter has img to document
		Boolean hasImage = GetHtmlCss.injectChapterHasImageLink(content, null);

		// remove unwanted content
		if (hasImage) {
			htmlPage = GetHtmlCss.filterHtml(htmlPage, cssRemoveContent);
			content = htmlPage.select("body").first().children();

			sb.append(Messages.getGlobalString("log.chapterHasImage"));
		} else {
			content = GetHtmlCss.filterHtml(content, cssRemoveContent);
		}

		StringBuilder sbTitle = new StringBuilder();
		int spaceID = id * 250 + 5;// space for auto index
		int i = 0;

		for (Iterator<Element> iterator = content.iterator(); iterator.hasNext();) {
			Element element = iterator.next();
			String title = CommonValue.getAnchorIDandTitle(spaceID,
					String.format(Messages.getGlobalString("log.page"), (id + 1), ++i));
			sbTitle.append(title);
			sb.append(CommonValue.getIDandTitleString(spaceID,
					String.format(Messages.getGlobalString("log.page"), (id + 1), i)));
			sb.append(element.html());
			spaceID++;
		}

		back.setTitle(sbTitle.toString());
		back.setContent(sb.toString());

		return back;
	}

	/**
	 * Use for Sstruyen.com
	 * 
	 * @param id
	 *            - number of chapter
	 * @param chapterUrl
	 * @param pageConfig
	 * @return {@link Chapter}
	 */
	public static Chapter getChapterTitleAndContentSSTruyen(int id, String chapterUrl, PageConfig pageConfig) {
		String cssChapterTitle = pageConfig.getCssQueryGetChapterTitle();
		String cssChapterContent = pageConfig.getCssQueryGetChapterContent();
		Boolean isEnableChapterSign = pageConfig.getIsEnableChapterSign();
		Chapter back = new Chapter();

		Document htmlPage = null;

		try {
			htmlPage = RequestUtil.get(chapterUrl, pageConfig);
		} catch (Exception e) {
			CommonLog.logError(e);
			return back;
		}

		Elements content = htmlPage.select(cssChapterContent);

		if (content == null) {
			return back;
		}
		String contentStr = content.html().replaceAll("\\;?var", "#");
		// Get chapterID & Time
		String[] arr = contentStr.split("#");
		String chapterID = arr[1].split("=")[1].trim();
		String time = arr[2].split("=")[1].trim();
		time = time.replaceAll("[\\-\\:\\s\\\"]", "");
		String urlParam = "http://sstruyen.com/doc-truyen/index.php?ajax=ct&id=" + chapterID + "&t=" + time;
		content = RequestUtil.get(urlParam, pageConfig).getAllElements(); // Jsoup.connect(urlParam).userAgent(Constant.USER_AGENT).get().getAllElements();
		htmlPage.children().stream().close();

		// get list img
		Boolean hasImage = GetHtmlCss.injectChapterHasImageLink(content, null);

		if (isEnableChapterSign) {
			if (htmlPage.select(cssChapterTitle).size() == 0) {
				back.setTitle(CommonValue.getChapterNameWithSignal(id + 1, ""));
			} else {
				back.setTitle(CommonValue.getChapterNameWithSignal(id + 1,
						htmlPage.select(cssChapterTitle).first().text().trim()));
			}
		} else if (!htmlPage.select(cssChapterTitle).isEmpty()) {
			back.setTitle(htmlPage.select(cssChapterTitle).first().text().trim());
		} else {
			back.setTitle("");
		}

		back.setContent(CommonValue.getIDandTitleString(id, back.getTitle(), content.html(), hasImage));

		return back;

	}

	/*
	 * get content ajax
	 */
	public static String getContentFromAjaxRequest(String url, String urlParameters,
			HashMap<String, String> requestHeaders, String method) throws IOException {

		byte[] postData = urlParameters.getBytes(StandardCharsets.UTF_8);

		URL u = new URL(url);
		HttpURLConnection conn = (HttpURLConnection) u.openConnection();
		conn.setDoOutput(true);
		conn.setInstanceFollowRedirects(false);
		conn.setRequestMethod(method);
		conn.setRequestProperty("User-Agent", Constant.USER_AGENT);

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

	/**
	 * Use for host truyencv.com only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - get button ShowChapter
	 * @return
	 * @throws IOException
	 */
	public static ArrayList<String> getListChaptersOnPageTruyenCV(String url, PageConfig pageConfig)
			throws IOException {
		Document htmlPage = null;
		String cssQuery = pageConfig.getCssQueryGetListChapter();
		ArrayList<String> listChapter = new ArrayList<>();
		try {
			htmlPage = RequestUtil.get(url, pageConfig);
		} catch (Exception e) {
			CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên truyencv thất bại");
			return listChapter;
		}
		String type = url.replaceAll("(https?:\\/\\/truyencv.com)", "");
		type = type.replaceAll("[\\-\\/]", " ").trim();

		String media_id = htmlPage.select(cssQuery).first().attr("onclick");
		media_id = media_id.split("[(,]")[1];

		String ajaxUrl = "https://truyencv.com/index.php";
		String urlParameters = "showChapter=1&media_id=" + media_id + "&number=9999&page=1&type=" + type;
		HashMap<String, String> requestHeaders = new HashMap<>();
		requestHeaders.put("Host", "truyencv.com");
		htmlPage = Jsoup.parse(RequestUtil.postFormData(ajaxUrl, urlParameters, requestHeaders, pageConfig));
		htmlPage.select("a").forEach((a) -> {
			listChapter.add(a.attr("href").toString());
		});
		return listChapter;
	}

	/*
	 * get content form forum type
	 */
	public static Element getTotalPageOfForum(Document docHTML, String txtUrl, String cssDivListChapter,
			String pagingPattern, JLabel lblStatus, JTextArea txtLog) throws IOException {
		String totalPageRegex = "";
		String totalPageCss = cssDivListChapter;
		String pagingPatternTmp = "";
		Element listChapter = docHTML.createElement("div");

		lblStatus.setText(Messages.getGlobalString("lblStatus.leechingTotalPage"));

		// handing totalPageCss
		if (totalPageCss.contains(";")) {
			totalPageCss = cssDivListChapter.substring(0, cssDivListChapter.indexOf(";"));
			totalPageRegex = cssDivListChapter.substring(cssDivListChapter.indexOf(";") + 1);
		}
		int totalPageInt = 1;

		// handing get totalPage
		String lastPageLink = docHTML.select(totalPageCss).first().attr("href");
		Pattern pattern = Pattern.compile(totalPageRegex);
		Matcher matcher = pattern.matcher(lastPageLink);
		// found number that is totalPage(between string)
		if (matcher.find()) {
			try {
				totalPageInt = Integer.parseInt(matcher.group(0).replaceAll("\\D", ""));

				txtLog.append(String.format(Messages.getGlobalString("txtLog.totalPage"), totalPageInt));

				txtLog.append(String.format(Messages.getGlobalString("txtLog.addLink"), txtUrl));

				if (pagingPattern.contains(";")) {
					pagingPatternTmp = pagingPattern.substring(0, pagingPattern.indexOf(";"));
				}

				// add link eachpage.
				listChapter.appendChild(docHTML.createElement("a").attr("href", txtUrl));

				for (int i = 1; i < totalPageInt; i++) {
					String urlTemp = txtUrl + pagingPatternTmp + (i + 1);
					if (pagingPattern.contains("{")) {

						if (pagingPatternTmp.contains("-")) {
							urlTemp = UrlHandler.getPagePatternUrl(pagingPattern, txtUrl,
									pagingPatternTmp.replaceFirst("\\{[\\w\\W]*\\}", String.valueOf(i)));
						} else {
							urlTemp = UrlHandler.getPagePatternUrl(pagingPattern, txtUrl,
									pagingPatternTmp.replaceFirst("\\{\\w*\\}", String.valueOf(i + 1)));
						}
					}
					listChapter.appendChild(docHTML.createElement("a").attr("href", urlTemp));

					lblStatus.setText(String.format(Messages.getGlobalString("txtLog.addLink"),
							(urlTemp.length() > 30 ? urlTemp.substring(0, 30) : urlTemp)));
					txtLog.append(String.format(Messages.getGlobalString("txtLog.addLink"), urlTemp));

				}
			} catch (NumberFormatException e) {
				totalPageInt = 1;
				e.printStackTrace();
			}
		}
		return listChapter;

	}

	/**
	 * Use for host wikidich.com only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - listchapter
	 * @return
	 * @throws IOException
	 */
	public static ArrayList<String> getListChaptersOnPageWikiDich(String url, PageConfig pageConfig)
			throws IOException {
		Document htmlPage = null;

		ArrayList<String> listChapter = new ArrayList<>();
		try {
			try {
				htmlPage = Jsoup.parse(GetHtmlCss.getHtmlStringFromURLbyCharset(url, pageConfig));
			} catch (Exception e) {
				CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên wikidich thất bại");
				return listChapter;
			}
			if (htmlPage != null) {

				String bookId = htmlPage.getElementById("bookId").val();
				String totalPageSelector = ".pagination li:last-child a[data-start]";
				Element totalPageEl = htmlPage.select(totalPageSelector).size() > 0
						? htmlPage.select(totalPageSelector).first() : null;

				String ajaxUrl = "http://wikidich.com/book/index";
				String templateParas = "?bookId=%s&start=%d&size=%d";

				if (totalPageEl != null) {
					int start = Integer.parseInt(totalPageEl.attr("data-start"));
					int size = Integer.parseInt(totalPageEl.attr("data-size"));
					int len = start / (size > 0 ? size : 1);
					for (int i = 0; i <= len; i++) {
						String tempUrl = ajaxUrl + String.format(templateParas, bookId, size * i, size);
						CommonUILog.info("GET " + tempUrl);
						htmlPage = Jsoup.parse(GetHtmlCss.getHtmlStringFromURLbyCharset(tempUrl, pageConfig));
						htmlPage.select("a.truncate").forEach((a) -> {
							String link = a.attr("href").toString();
							if (link.length() < 5) {
								if (a.hasAttr("data-href")) {
									link = a.attr("data-href").toString();
								}
							}
							listChapter.add(link);
						});
						CommonUILog.info("DONE " + tempUrl);
						Thread.sleep(CommonValue.SLEEP_TIME);
					}

				} else {
					// not paging
					String tempUrl = ajaxUrl + String.format(templateParas, bookId, 0, 501);
					CommonUILog.info("GET " + tempUrl);
					htmlPage = Jsoup.parse(GetHtmlCss.getHtmlStringFromURLbyCharset(tempUrl, pageConfig));
					htmlPage.select("a.truncate").forEach((a) -> {
						String link = a.attr("href").toString();
						if (link.length() < 5) {
							if (a.hasAttr("data-href")) {
								link = a.attr("data-href").toString();
							}
						}
						listChapter.add(link);
					});
					CommonUILog.info("DONE " + tempUrl);
				}
			}

		} catch (Exception e1) {
			CommonExceptionHandle.HandleException(e1, "Lấy thông tin truyện trên wikidich thất bại");
			e1.printStackTrace();
		}
		return listChapter;
	}

	/**
	 * Use for host truyen.tangthuvien.com only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - get button ShowChapter
	 * @return
	 * @throws IOException
	 */
	public static ArrayList<String> getListChaptersOnPageTruyenTangThuVien(String url, PageConfig pageConfig)
			throws IOException {
		Document htmlPage = null;

		ArrayList<String> listChapter = new ArrayList<>();
		try {
			try {
				htmlPage = RequestUtil.get(url, pageConfig);
			} catch (Exception e) {
				CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên truyen.tangthuvien.com thất bại");
				return listChapter;
			}
			String bookId = htmlPage.getElementsByAttributeValue("name", "story_id").val();
			String ajaxUrl = "https://truyen.tangthuvien.vn/story/chapters";
			String templateParas = "?story_id=%s&chapter_id=1";

			// not paging
			String tempUrl = ajaxUrl + String.format(templateParas, bookId);

			CommonUILog.info("GET " + tempUrl);
			htmlPage = Jsoup.parse(GetHtmlCss.getHtmlStringFromURLbyCharset(tempUrl, pageConfig));
			htmlPage.select("a").forEach((a) -> {
				String link = a.attr("href").toString();
				listChapter.add(link);
			});
			htmlPage.children().stream().close();
			CommonUILog.info("DONE " + tempUrl);

		} catch (Exception e1) {
			CommonExceptionHandle.HandleException(e1, "Lấy thông tin truyện trên truyen.tangthuvien.com thất bại");
			e1.printStackTrace();
		}
		return listChapter;
	}

	/**
	 * Use for host tangthucac.com only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - get button ShowChapter
	 * @return
	 * @throws IOException
	 */
	public static Chapter getChapterTitleTangThuCacDotCom(int index, String chapterUrl, PageConfig pageConfig) {
		String cssChapterTitle = pageConfig.getCssQueryGetChapterTitle();
		String cssRemoveContent = pageConfig.getCssFilter();
		Boolean isEnableChapterSign = pageConfig.getIsEnableChapterSign();

		Chapter back = new Chapter();
		Document htmlPage = null;
		try {
			htmlPage = RequestUtil.get(chapterUrl, pageConfig);
			String title = htmlPage.select(cssChapterTitle).html();
			String tempId = chapterUrl.substring(0, chapterUrl.lastIndexOf("chuong") - 1);
			String id = tempId.substring(tempId.lastIndexOf("/") + 1);
			String ajaxUrl = String.format("https://tangthucac.com/chapter/%s/", id);
			String templateParas = "id=%s-%d";

			templateParas = String.format(templateParas, id, index);
			HashMap<String, String> requestHeaders = new HashMap<>();
			requestHeaders.put("Host", "tangthucac.com");
			requestHeaders.put("Origin", "https://tangthucac.com");
			htmlPage = Jsoup.parse(getContentFromAjaxRequest(ajaxUrl, templateParas, requestHeaders, "POST"));
			Elements content = htmlPage.select("body");

			// get list img
			Boolean hasImage = GetHtmlCss.injectChapterHasImageLink(content, null);

			// remove unwanted content
			GetHtmlCss.filterHtml(content, cssRemoveContent);

			if (isEnableChapterSign) {
				if (title == "") {
					back.setTitle(CommonValue.getChapterNameWithSignal(index - 1, ""));
				} else {
					back.setTitle(CommonValue.getChapterNameWithSignal(index - 1, title));
				}
			} else if (title != "") {
				back.setTitle(title);
			} else {
				back.setTitle("");
			}

			back.setContent(CommonValue.getIDandTitleString(index - 1, back.getTitle(), content.html(), hasImage));

		} catch (Exception e) {
			CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên tangthucac.com thất bại");
			e.printStackTrace();
			back = null;
		}

		return back;
	}

	/**
	 * Use for host wikidich.com only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - listchapter
	 * @return
	 * @throws IOException
	 */
	public static ArrayList<String> getListChaptersOnPageTangThuCacDotCom(String url, PageConfig pageConfig)
			throws IOException {
		Document htmlPage = null;
		ArrayList<String> listChapter = new ArrayList<>();
		try {
			try {
				htmlPage = RequestUtil.get(url, pageConfig);
			} catch (Exception e) {
				CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên tangthucac.com thất bại");
				return listChapter;
			}
			String bookId = "";
			Element elBookID = htmlPage.select("[data-bid]").first();
			if (elBookID != null) {
				bookId = elBookID.attr("data-bid");
			}

			String ajaxUrl = "https://tangthucac.com/ajax/getchapterlist/";
			String templateParas = "page=%d&id=%s";

			for (int i = 1; i <= 10000; i++) {
				CommonUILog.info("GET page " + i);

				htmlPage = Jsoup.parse(
						getContentFromAjaxRequest(ajaxUrl, String.format(templateParas, i, bookId), null, "POST"));
				htmlPage.children().stream().close();

				Elements lstTagA = htmlPage.select("a");
				if (lstTagA.size() > 0) {
					// when overload this site return to no chapter
					lstTagA.forEach((a) -> {
						listChapter.add(a.attr("href").toString());
					});

					CommonUILog.info("DONE page " + i);
				} else {
					CommonUILog.info("DONE All page load.");
					break;
				}
				Thread.sleep(CommonValue.SLEEP_TIME);
			}

		} catch (Exception e1) {
			CommonExceptionHandle.HandleException(e1, "Lấy thông tin truyện trên wikidich thất bại");
			e1.printStackTrace();
		}
		return listChapter;
	}

	/**
	 * Use for host truyendich.org only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - listchapter
	 * @return
	 * @throws IOException
	 */
	public static ArrayList<String> getListChaptersOnPageTruyenDichDotOrg(String url, PageConfig pageConfig)
			throws IOException {
		ArrayList<String> listChapter = new ArrayList<>();
		try {
			String truyendichOrgHost = CommonValue.getTruyenDichOrgHost();
			String urlGetId = truyendichOrgHost + "/api/item/%s";
			String chapterUrl = truyendichOrgHost + "/api/chapter/";
			String tempUrl = "";
			url = url.trim();
			if (url.endsWith("/")) {
				url = url.substring(0, url.length() - 1);
			}
			String bookId = url.substring(url.lastIndexOf("/") + 1);
			chapterUrl += bookId;
			String lastestChapter = "0";
			int intLastestChapter = 0;
			HashMap<String, String> header = new HashMap<>();
			header.put("Origin", "http://truyendich.org");
			header.put("Content-Type", "application/json");
			try {
				tempUrl = String.format(urlGetId, bookId);
				String json = getContentFromAjaxRequest(tempUrl, "", header, "GET");
				JSONObject obj = new JSONObject(json);
				lastestChapter = obj.getJSONObject("item").getString("latest_chapter");
				intLastestChapter = Integer.parseInt(lastestChapter);
			} catch (Exception e) {
				CommonLog.logInfo("Laster chapter: " + lastestChapter);
				CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên truyendich.org thất bại");
				return listChapter;
			}

			for (int i = 1; i <= intLastestChapter; i++) {
				listChapter.add(String.format("%s/%d", chapterUrl, i));
			}

		} catch (Exception e1) {
			CommonExceptionHandle.HandleException(e1, "Lấy thông tin truyện trên truyendich.org thất bại");
			e1.printStackTrace();
		}
		return listChapter;
	}

	/**
	 * Use for host tangthucac.com only
	 * 
	 * @param url
	 * @param cssQuery
	 *            - get button ShowChapter
	 * @return null - nothing to get
	 */
	public static Chapter getChapterTitleTruyenDichDotOrg(int index, String chapterUrl, PageConfig pageConfig) {
		Boolean isEnableChapterSign = pageConfig.getIsEnableChapterSign();
		Chapter back = new Chapter();
		try {
			String json = getContentFromAjaxRequest(chapterUrl, "", null, "GET");
			JSONObject obj = new JSONObject(json);
			obj = obj.getJSONObject("chapter");
			String title = obj.getString("name"), content = obj.getString("content");
			if (isEnableChapterSign) {
				if (title == "") {
					back.setTitle(CommonValue.getChapterNameWithSignal(index - 1, ""));
				} else {
					back.setTitle(CommonValue.getChapterNameWithSignal(index - 1, title));
				}
			} else if (title != "") {
				title = String.format("%s %d: %s", Messages.getGlobalString("chapter.Title"), index + 1, title);
				back.setTitle(title);
			} else {
				back.setTitle("");
			}

			back.setContent(CommonValue.getIDandTitleString(index - 1, back.getTitle(), content, false));

		} catch (Exception e) {
			CommonExceptionHandle.HandleException(e, "Lấy thông tin truyện trên truyendich.com thất bại");
			e.printStackTrace();
			back = null;
		}

		return back;
	}

}
