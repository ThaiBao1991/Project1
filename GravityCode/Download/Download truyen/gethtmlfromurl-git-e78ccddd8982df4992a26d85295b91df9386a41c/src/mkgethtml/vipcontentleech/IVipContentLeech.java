/**
 * 
 */
package mkgethtml.vipcontentleech;

import java.net.URL;

import org.jsoup.nodes.Document;

import models.LoginInfo;
import models.PageConfig;

/**
 * @author nxcuo Contains main method to leech content for mutil host
 * @since 09.07.2018
 */
public interface IVipContentLeech {
	// /**
	// * get VIP content and fill into document
	// *
	// * @param document
	// * @param url
	// * @param cssChapterTitle
	// * @param cssChapterContent
	// * @param isEnableChapterSign
	// * @param isUseJsoupGet
	// */
	// void leechVipContent(Document document, String url, String
	// cssChapterTitle, String cssChapterContent,
	// Boolean isEnableChapterSign, Boolean isUseJsoupGet);

	/**
	 * get VIP content and fill into document
	 * 
	 * @param document
	 * @param url
	 * @param loginInfo
	 *            - login data of site
	 * @param pageConfig
	 */
	void leechVipContent(Document document, URL url, LoginInfo loginInfo, PageConfig pageConfig);
}
