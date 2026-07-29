package thread;

import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JProgressBar;
import javax.swing.JTextArea;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import common.Enumeration.EnumConfigKey;
import common.Enumeration.UIType;
import log.CommonUILog;
import main.DownloadRange;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.GetHtmlCss;
import mkgethtml.SettingOption;
import models.PageConfig;
import utils.UrlHandler;

public class TManual extends TAuto implements Runnable {

	public TManual() {
		super();
	}

	public TManual(JButton btnCancel, JButton btnDownload, JButton btnResume, String txtUrl, String fileName,
			JLabel lblStatus, JTextArea txtLog, JProgressBar progressBar, PageConfig pageConfig, String ebookInfo,
			Boolean isDivideFile) {
		super(btnCancel, btnDownload, btnResume, txtUrl, fileName, lblStatus, txtLog, progressBar, ebookInfo,
				isDivideFile, pageConfig);
		type = 1;
		p = pageConfig;

	}

	@Override
	int getListChapter() {
		progressBar.setMaximum(100);
		progressBar.setValue(0);

		// if config encoding already is UTF-8 then do nothing, else setup it
		if (!SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING)
				.equals(Constant.DEFAULT_ENCODING)) {
			Config.put(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING);
		}
		Document docHTML = null;
		try {
			// lablel
			// log for Range Download
			if (DownloadRange.visiable) {
				CommonUILog.info(
						"\n-----------------------------------------------------\r\n"
								+ "ĐÃ CHỌN TẢI TRONG PHẠM VI...ĐANG CHỜ DANH SÁCH CHƯƠNG\r\n"
								+ "-----------------------------------------------------\r\n",
						UIType.ManualUIWindow, log);
			}
			lblStatus.setText("Kiểm tra chuỗi nhập vào");
			CommonUILog.info("Kiểm tra...\n", UIType.ManualUIWindow, log);

			try {
				docHTML = Jsoup.parse(txtUrl);
				// update ENCONDING
				if (!docHTML.charset().name()
						.equals(SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING))) {
					Config.put(EnumConfigKey.ENCODING, docHTML.charset().name());
				}

				encoding = SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING);
			} catch (Exception e) {
				CommonUILog.error("Lỗi không thể chuyển đổi sang tài liệu HTML" + "\n\tHãy chọn đúng Host."
						+ "\nCóp toàn bộ trang HTML: " + "\n\tChuột phải -> ViewPageSource(Xem Nguồn Trang)"
						+ "\n\tCTRL + A -> CTRL + C, rồi dán vào InputHTML", UIType.ManualUIWindow, log);
			}

			// using for pattern get.
			ArrayList<String> arr = new ArrayList<>();
			String cssQueryGetListChapter = p.getCssQueryGetListChapter().replaceAll("\\$([\\w\\d\\\\W\\D=\\&\\;])*",
					"");
			if (p.getCssQueryGetListChapter().contains("{")) {
				arr = GetHtmlCss.getSpecialStringFromQuery(p.getCssQueryGetListChapter());
				cssQueryGetListChapter = cssQueryGetListChapter.substring(0, cssQueryGetListChapter.indexOf("{"));
			}

			Element listTagAUrl = null;
			// if has pattern
			if (p.getCssQueryGetListChapter().contains("{")) {
				listTagAUrl = GetHtmlCss.getListTagAUrlSpecialCssQuery(docHTML, cssQueryGetListChapter, arr);
			} else {
				listTagAUrl = docHTML.select(p.getCssQueryGetListChapter()).first();
			}

			// perform change url
			if (!p.getIsChapterLinkAsolute()) {
				listTagAUrl.select("a").iterator().forEachRemaining((link) -> {
					link.attr("href",
							UrlHandler.normalizeHostAndPath(p.getPageCode(), link.attr("href"), p.getUrlPageTest()));
				});
			}

			storyTitle = docHTML.title();

			int size = listTagAUrl.select("a").size();

			if (size < 1) {
				CommonUILog.warn("Không tìm thấy đường dẫn chương" + "\n\tHãy chọn đúng Host."
						+ "\nCóp toàn bộ trang HTML: " + "\n\tChuột phải -> ViewPageSource(Xem Nguồn Trang)"
						+ "\n\tCTRL + A -> CTRL + C, rồi dán vào InputHTML" + "\n* Hãy chắc chắn là đã config đúng",
						UIType.ManualUIWindow, log);
				return -1;
			}

			lblStatus.setText("Scanned page index: " + size + "/" + size + " complete");
			CommonUILog.info(lblStatus.getText() + "\n", UIType.ManualUIWindow, log);

			lblStatus.setText("Scanning chapter url...\n");
			CommonUILog.info("Đang quét đường dẫn chapter...\n", UIType.ManualUIWindow, log);

			String tempURL = "";
			for (int i = 0; i < size; i++) {
				// check real link.
				tempURL = listTagAUrl.select("a").eq(i).attr("href").toString().trim();
				if (!tempURL.startsWith("http")) {
					tempURL = UrlHandler.normalizeHost(p.getPageCode(), p.getUrlPageTest())
							+ UrlHandler.normalizePath(tempURL);
				}
				if (tempURL.length() > 20) {
					if (!listChapter.contains(tempURL)) {

						listChapter.add(tempURL);
						CommonUILog.info("Tìm thấy: " + tempURL + "\n", UIType.ManualUIWindow, log);
					} else {
						CommonUILog.warn("Link bị trùng: " + tempURL + ", đã loại bỏ.\n", UIType.ManualUIWindow, log);
					}
				}

			}
			// size
			size = listChapter.size();
			interval = size / 100;
			if (interval == 0) {
				interval = 1;
			}
		} catch (Exception e) {
			CommonUILog.error(e.getMessage(), UIType.ManualUIWindow, log);
			return -1;
		}
		return 0;
	}

}
