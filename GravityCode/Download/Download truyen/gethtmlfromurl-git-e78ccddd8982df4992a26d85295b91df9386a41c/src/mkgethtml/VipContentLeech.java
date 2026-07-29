package mkgethtml;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;

import org.jsoup.nodes.Document;

import log.CommonLog;
import mk.constant.Constant;
import mkgethtml.vipcontentleech.IVipContentLeech;
import mkgethtml.vipcontentleech.TruyenYYVipContentLeech;
import models.LoginInfo;
import models.PageConfig;

/**
 * check and leech vip content
 * 
 * @author nxcuo
 *
 */
public class VipContentLeech {
	/**
	 * list container of VIP content leech Class
	 */
	private static HashMap<String, IVipContentLeech> _listVipContentLeech = new HashMap<>();

	/**
	 * leech vip content
	 * 
	 * @param document
	 * @param url
	 */
	public static void leechVipContent(Document document, String url, PageConfig pageConfig) {
		if (document != null) {
			URL u = null;
			String pageCode = "";
			try {
				u = new URL(url);
				pageCode = u.getHost();
			} catch (MalformedURLException e) {
				e.printStackTrace();
				CommonLog.logError(e);
			}
			LoginInfo loginInfo = Config.getLoginInfoByPageCode(pageCode);
			// check login
			Boolean isLogin = loginInfo != null ? (!loginInfo.getCookies().isEmpty() ? true : false) : false;

			if (_listVipContentLeech.size() > Constant.CACHE_VIP_SIZE) {
				// if cache host over size -> flush cache
				_listVipContentLeech.clear();

			}

			if (!pageCode.isEmpty() && isLogin) {
				switch (pageCode) {
				case "truyenyy.com":

					if (!_listVipContentLeech.containsKey(pageCode)) {
						_listVipContentLeech.put(pageCode, new TruyenYYVipContentLeech());
					}
					_listVipContentLeech.get(pageCode).leechVipContent(document, u, loginInfo, pageConfig);

					break;

				default:
					break;
				}

			}

		}
	}

}
