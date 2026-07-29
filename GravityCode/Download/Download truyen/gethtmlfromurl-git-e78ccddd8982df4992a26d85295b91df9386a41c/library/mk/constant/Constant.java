package mk.constant;

/**
 * All constant
 * 
 * @author nxcuo
 *
 */
public class Constant {
	/**
	 * Vietnamese language
	 */
	public static final String DEFAULT_LANGUAGE = "vi";
	/**
	 * default line height
	 */
	public static final int DEFAULT_LINE_HEIGH = 16;
	/**
	 * default encoding
	 */
	public static final String DEFAULT_ENCODING = "UTF-8";

	/**
	 * default max-connection
	 */
	public static final int DEFAULT_MAX_CONNECTION = 2;
	/**
	 * default time out (second)
	 */
	public static final int DEFAULT_TIME_OUT = 60;
	/**
	 * default sleep time(mini second)
	 */
	public static final int DEFAULT_SLEEP_TIME = 60;

	/**
	 * default sleep time(mini second)
	 */
	public static final String DEFAULT_RECENT_FOLDER = "D:/";

	/**
	 * default two level chapter title
	 */
	public static final String DEFAULT_TWO_LEVEL_CHAPTER_TITLE = "Chương";
	/**
	 * default two level break chapter count
	 */
	public static final int DEFAULT_TWO_LEVEL_BREAK_CHAPTER_COUNT = 50;

	/**
	 * default ebook info
	 */
	public static final String DEFAULT_EBOOK_INFO = "";

	/**
	 * README.txt file on sourceforce
	 */
	public static final String SOURCEFORCE_UPDATE_FILE = "UPDATE.txt";
	/**
	 * UPDATE.txt file on sourceforce
	 */
	public static final String SOURCEFORCE_README_FILE = "README.txt";

	/**
	 * NEWSHOST.txt file on sourceforce
	 */
	public static final String SOURCEFORCE_NEWSHOST_FILE = "NEWSHOST.txt";

	/**
	 * NEWS.txt file on sourceforce
	 */
	public static final String SOURCEFORCE_NEWS_FILE = "NEWS.txt";

	/**
	 * userConfig.data file on local
	 */
	public static final String CONFIG_USER_SETTING_FILE = "userConfig.data";
	/**
	 * ghfuConfig.json file on sourceforce
	 */
	public static final String CONFIG_DATASITE_FILE = "ghfuConfig.json";

	/**
	 * link direct to sourceforce.net/ghfu
	 */
	public static final String SOURCEFORCE_DIRECT_LINK = "https://master.dl.sourceforge.net/project/gethtmlfromurl/";

	/**
	 * app title prefix
	 */
	public static final String APP_TITLE = "GetTextFromHtml-V";

	/**
	 * temp download folder prefix
	 */
	public static final String TMP_PREFIX = "GHFU";

	/**
	 * user-agent fake as an browser
	 */
	public static final String USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36";

	/**
	 * Size of cache list vip content leech size
	 */
	public static final int CACHE_VIP_SIZE = 30;

	/**
	 * System line separator
	 */
	public static final String LINE_BREAK = System.getProperty("line.separator");
}
