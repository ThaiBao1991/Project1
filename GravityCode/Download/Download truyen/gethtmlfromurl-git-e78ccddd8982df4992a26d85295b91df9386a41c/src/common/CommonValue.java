package common;

import java.io.File;
import java.util.ResourceBundle;

import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class CommonValue {
	static String HTML_HEAD_O = "";
	static String HTML_HEAD_C = "";
	static String HTML_C = "";
	static String HTML_ANCHOR_O = "";
	static String HTML_ANCHOR_C = "";
	static String HTML_ID_O = "";
	static String HTML_ID_C = "";
	static String UNNAME_CHAPTER = "Chapter ";
	static String SIGNAL_CHAPTER_BEGIN = "MKI";
	static String HTML_EBOOK_O = "";
	static String HTML_EBOOK_CREATOR_O = "";
	static String HTML_EBOOK_P_C = "";
	static String HTML_EBOOK_CONVERTER_O = "";
	static String HTML_EBOOK_STORY_O = "";
	static String HTML_EBOOK_AUTHOR_O = "";
	static String HTML_EBOOK_STATUS_O = "";
	static String HTML_EBOOK_SOURCE_O = "";
	static String HTML_EBOOK_INTRO_O = "";
	static String HTML_EBOOK_C = "";
	static String CONFIG_TRUYENDICH_ORG_API_HOST = "";

	static Boolean isInit = false;
	static ResourceBundle bundle;

	/**
	 * current app version to check update
	 */
	public static final String APP_VERSION = "1.5.6";

	/**
	 * timeout for request
	 */
	private static int TIME_OUT = Constant.DEFAULT_TIME_OUT;
	/**
	 * time sleep between threading
	 */
	public static int SLEEP_TIME = Constant.DEFAULT_SLEEP_TIME;

	public static void AutoConfigCharsetForDownload() {

	}

	/**
	 * gen html anchor id and title
	 * 
	 * @param anchorID
	 *            - number of anchor
	 * @param title
	 *            - title text for this
	 * @return String title
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getAnchorIDandTitle(int anchorID, String title) {
		return HTML_ANCHOR_O + anchorID + "\">" + title + HTML_ANCHOR_C;
	}

	/**
	 * get current file app.jar
	 * 
	 * @return {@link File}
	 * @author mkbyme Oct 15, 2017
	 */
	public static File getAppJARFile() {
		return new File(System.getProperty("java.class.path"));
	}

	/**
	 * commbine apptitle and appversion
	 * 
	 * @return apptitle with version
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getAppName() {
		return Constant.APP_TITLE + APP_VERSION;
	}

	/**
	 * get chapter name with signal before
	 * 
	 * @param id
	 *            - number of signal
	 * @param title
	 *            - chapter title
	 * @return String title contain title and signal
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getChapterNameWithSignal(int id, String title) {
		if (title.trim().isEmpty()) {
			return SIGNAL_CHAPTER_BEGIN + id + " " + UNNAME_CHAPTER + id;
		}
		return SIGNAL_CHAPTER_BEGIN + id + " " + title;
	}

	/**
	 * return link of config.data on sourceforce server
	 * 
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getDownloadLinkConfigFile() {
		return getSourceForceDirectURL(Constant.CONFIG_DATASITE_FILE);
	}

	/**
	 * direct url of file on sourceforce.net
	 * 
	 * @param fileName
	 *            - name of file
	 * @return String url of file
	 * @author mkbyme Jan 30, 2019
	 */
	public static String getSourceForceDirectURL(String fileName) {
		return Constant.SOURCEFORCE_DIRECT_LINK + fileName + "?viasf=1";
	}

	/**
	 * return auther name in html
	 * 
	 * @param author
	 *            - author name
	 * @return String author in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookAuthorHTML(String author) {
		return HTML_EBOOK_AUTHOR_O + author + HTML_EBOOK_P_C;
	}

	/**
	 * return converter name in html
	 * 
	 * @param converterName
	 *            - converter name
	 * @return String converterName in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookConverterHTML(String converterName) {
		return HTML_EBOOK_CONVERTER_O + converterName + HTML_EBOOK_P_C;
	}

	/**
	 * return creator name in html
	 * 
	 * @param creatorName
	 * @returnString creatorName in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookCreatorHTML(String creatorName) {
		return HTML_EBOOK_CREATOR_O + creatorName + HTML_EBOOK_P_C;
	}

	/**
	 * return info in html
	 * 
	 * @param info
	 * @returnString info in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookDescriptionHTML(String info) {
		return HTML_EBOOK_INTRO_O + info + HTML_EBOOK_P_C;
	}

	/**
	 * return closing ebook info when save in html format
	 * 
	 * @return html closing
	 */
	public static String getEbookInfoClose() {
		return HTML_EBOOK_C;
	}

	/**
	 * return opening file when save in html format
	 * 
	 * @return html opening
	 */
	public static String getEbookInfoOpen() {
		return HTML_EBOOK_O;
	}

	/**
	 * return source in html
	 * 
	 * @param source
	 * @returnString source in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookSourceHTML(String source) {
		return HTML_EBOOK_SOURCE_O + source + HTML_EBOOK_P_C;
	}

	/**
	 * return ebook status in html
	 * 
	 * @param status
	 * @returnString ebook status in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookStatusHTML(String status) {
		return HTML_EBOOK_STATUS_O + status + HTML_EBOOK_P_C;
	}

	/**
	 * return ebook name in html
	 * 
	 * @param storyName
	 * @returnString ebook storyName in html format
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getEbookStoryNameHTML(String storyName) {
		return HTML_EBOOK_STORY_O + storyName + HTML_EBOOK_P_C;
	}

	/**
	 * return closing html file content when save in html format
	 * 
	 * @return html closing
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getHtmlCloseString() {
		return HTML_C;
	}

	/**
	 * return opening html file content with title when save in html format
	 * 
	 * @param title
	 *            - title of html
	 * 
	 * @return opening html
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getHtmlOpenString(String title) {
		return HTML_HEAD_O + "<meta http-equiv=\"Content-Type\" content=\"text/html; charset="
				+ SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING) + "\" />"
				+ "<style>body{line-height:"
				+ SettingOption.getInt(EnumConfigKey.LINE_HEIGHT, Constant.DEFAULT_LINE_HEIGH) + "pt;}</style>"
				+ "<title>" + title + " - Created with " + getAppName() + " - Written by Mkbyme" + HTML_HEAD_C;
	}

	/**
	 * get id and title
	 * 
	 * @param id
	 *            - number of index
	 * @param title
	 *            - string
	 * @return string
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getIDandTitleString(int id, String title) {
		return HTML_ID_O + id + "\">" + title + HTML_ID_C;
	}

	/**
	 * get id and title with content
	 * 
	 * @param id
	 *            - id
	 * @param title
	 *            - title
	 * @param content
	 * @param isShowChapterHasImageTip
	 * @return String
	 * @author mkbyme Jan 27, 2019
	 */
	public static String getIDandTitleString(int id, String title, String content, Boolean isShowChapterHasImageTip) {

		if (isShowChapterHasImageTip) {
			content = Messages.getGlobalString("log.chapterHasImage") + content;
		}
		return HTML_ID_O + id + "\">" + title + HTML_ID_C + content;
	}

	/**
	 * get current jar path
	 * 
	 * @return jar path
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getJarPath() {
		return Config.class.getProtectionDomain().getCodeSource().getLocation().getHost();
	}

	/**
	 * get number of thread on mutil thread mode
	 * 
	 * @return number
	 * @author mkbyme Oct 15, 2017
	 */
	public static int getNumThread() {
		return SettingOption.getInt(EnumConfigKey.MAXCONNECTION, Constant.DEFAULT_MAX_CONNECTION);
	}

	/**
	 * Before using Method of CommandValue has STRING LOAD FROM FILE Should call
	 * this method 1st
	 * 
	 * @author mkbyme Oct 15, 2017
	 */
	public static void initValue() {
		bundle = ResourceBundle.getBundle("common.commandValue");
		HTML_HEAD_O = bundle.getString("HTML_HEAD_O");
		HTML_HEAD_C = bundle.getString("HTML_HEAD_C");
		HTML_C = bundle.getString("HTML_C");
		HTML_ANCHOR_O = bundle.getString("HTML_ANCHOR_O");
		HTML_ANCHOR_C = bundle.getString("HTML_ANCHOR_C");
		HTML_ID_O = bundle.getString("HTML_ID_O");
		HTML_ID_C = bundle.getString("HTML_ID_C");

		HTML_EBOOK_O = bundle.getString("HTML_EBOOK_O");

		HTML_EBOOK_CREATOR_O = bundle.getString("HTML_EBOOK_CREATOR_O");
		HTML_EBOOK_P_C = bundle.getString("HTML_EBOOK_P_C");
		HTML_EBOOK_CONVERTER_O = bundle.getString("HTML_EBOOK_CONVERTER_O");
		HTML_EBOOK_SOURCE_O = bundle.getString("HTML_EBOOK_SOURCE_O");
		HTML_EBOOK_AUTHOR_O = bundle.getString("HTML_EBOOK_AUTHOR_O");
		HTML_EBOOK_STORY_O = bundle.getString("HTML_EBOOK_STORY_O");
		HTML_EBOOK_STATUS_O = bundle.getString("HTML_EBOOK_STATUS_O");
		HTML_EBOOK_INTRO_O = bundle.getString("HTML_EBOOK_INTRO_O");

		HTML_EBOOK_C = bundle.getString("HTML_EBOOK_C");

		// list config
		CONFIG_TRUYENDICH_ORG_API_HOST = bundle.getString("CONFIG_TRUYENDICH_ORG_API_HOST");
		// Download Settings
		try {
			TIME_OUT = SettingOption.getInt(EnumConfigKey.TIME_OUT, Constant.DEFAULT_TIME_OUT);
			SLEEP_TIME = SettingOption.getInt(EnumConfigKey.SLEEP_TIME, Constant.DEFAULT_SLEEP_TIME);
		} catch (NullPointerException e) {
			Config.put(EnumConfigKey.TIME_OUT, TIME_OUT);
			Config.put(EnumConfigKey.SLEEP_TIME, SLEEP_TIME);
		}

	}

	/**
	 * update config data file
	 * 
	 * @param timeout
	 *            - in minisecond
	 * @param sleepTime
	 *            - in minisecond
	 * @author mkbyme Oct 15, 2017
	 */
	public static void updateDownloadConfig(int timeout, int sleepTime) {
		TIME_OUT = timeout;
		SLEEP_TIME = sleepTime;
		Config.put(EnumConfigKey.TIME_OUT, TIME_OUT);
		Config.put(EnumConfigKey.SLEEP_TIME, SLEEP_TIME);
		Config.saveConfig(Enumeration.ConfigType.Setting);
	}

	/**
	 * gen html anchor id and title for table of content level 1
	 * 
	 * @param anchorID
	 *            - number of anchor
	 * @param title
	 *            - title text for this
	 * @param isHead
	 *            - is head of Table of content level 1 (this has two anchor,
	 *            head and body)
	 * @return String title
	 * @author mkbyme Oct 15, 2017
	 */
	public static String getAnchorIDandTitleForTOCLV1(int anchorID, int breakCount, String title, Boolean isHead) {
		// anchor run from 0 -> and we want show from 1
		title = String.format("%s %s → %s", title, anchorID + 1, anchorID + breakCount + (anchorID == 0 ? -1 : 0));

		return String.format("%s%s%s\" class=\"toclv2\" id=\"%s%s\">%s%s", HTML_ANCHOR_O, (isHead ? "h" : "b"),
				anchorID, (isHead ? "b" : "h"), anchorID, title, HTML_ANCHOR_C);

	}

	/**
	 * Check that need to write down new level 1 TOC if true
	 * 
	 * @param anchorID
	 *            - current index of anchor(start from 0)
	 * @param breakCount
	 *            - break chapter level 1 count
	 * @param totalChapterCount
	 *            -
	 * @return true if run in breakCount
	 */
	public static Boolean checkIsTOCLV1RunIn(int anchorID, int breakCount, int totalChapterCount) {
		Boolean isRunIn = false;
		anchorID++;
		if (anchorID == 1 || anchorID % breakCount == 0) {
			isRunIn = true;
		}

		return isRunIn;
	}

	/**
	 * return request timeout
	 * 
	 * @return number
	 * @author mkbyme Jan 30, 2019
	 */
	public static int getTimeout() {
		return TIME_OUT * 1000;
	}

	/**
	 * Get truyendich.org api host:port
	 * 
	 * @return
	 */
	public static String getTruyenDichOrgHost() {
		return CONFIG_TRUYENDICH_ORG_API_HOST;
	}

}
