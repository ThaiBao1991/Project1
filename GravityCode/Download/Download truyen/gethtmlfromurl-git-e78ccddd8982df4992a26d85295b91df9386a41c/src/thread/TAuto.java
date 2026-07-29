package thread;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Date;
import java.util.Scanner;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JProgressBar;
import javax.swing.JTextArea;
import javax.swing.SpinnerNumberModel;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import common.CommonExceptionHandle;
import common.CommonValue;
import common.Enumeration.EnumConfigKey;
import log.CommonUILog;
import main.DownloadRange;
import main.JShowHelpDialog;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.GetHtmlCsMix;
import mkgethtml.GetHtmlCss;
import mkgethtml.SettingOption;
import models.Chapter;
import models.PageConfig;
import resource.text.Messages;
import utils.RequestUtil;
import utils.UrlHandler;

/**
 * @author Adminz
 *
 */
/**
 * @author Adminz
 *
 */
public class TAuto implements Runnable {
	Thread task;
	String fileName;
	String tempFileName;
	String txtUrl;
	String ebookInfo;
	JButton btnCancel, btnDownload, btnResume;
	String storyTitle = "";
	JLabel lblStatus;
	public JTextArea log;
	JProgressBar progressBar;
	int count = 0;
	int interval = 0;
	int size = 0;
	int type = 0;
	Boolean isFinish = false;

	final Object lockO = new Object();
	String encoding = "UTF-8";
	Boolean isShowDoCapchaDiaglog = false;
	Boolean isDoneCapcha = false;
	Boolean isDivideFile = false;
	String extension = "html";
	String folderMutilFilePath = "";
	String fileNameWithoutExtension = "";
	/**
	 * Count to show help tips on error
	 */
	public int DownloadFailedCount = 0;
	ArrayList<MutilDownload> mutilThread;

	/**
	 * Use for TOC two level
	 */
	Boolean isUseTwoLevelForTOC = false;
	String twoLevelChapterTitle = "";
	int twoLevelBreakChapterCount = 50;

	public ArrayList<String> listChapter;
	public PageConfig p;
	public String storyTempFolder = "";
	public int indexOfStartCut = 0;
	public int indexOfEndCut = 0;

	public TAuto() {
	}

	public TAuto(JButton btnCancel, JButton btnDownload, JButton btnResume, String txtUrl, String fileName,
			JLabel lblStatus, JTextArea txtLog, JProgressBar progressBar, String ebookInfo, Boolean isDivideFile,
			PageConfig config) {

		this.txtUrl = txtUrl;
		this.ebookInfo = ebookInfo;
		this.fileName = fileName;
		this.lblStatus = lblStatus;
		this.log = txtLog;
		this.progressBar = progressBar;
		this.btnCancel = btnCancel;
		this.btnDownload = btnDownload;
		this.btnResume = btnResume;
		this.isShowDoCapchaDiaglog = false;
		this.isDoneCapcha = false;
		this.isDivideFile = isDivideFile;
		this.DownloadFailedCount = 0;
		this.indexOfStartCut = 0;
		this.indexOfEndCut = 0;

		// mkbyme 2018.12.09 - add for 2 level of TOC
		this.twoLevelBreakChapterCount = SettingOption.getInt(EnumConfigKey.TWO_LEVEL_BREAK_CHAPTER_COUNT,
				Constant.DEFAULT_TWO_LEVEL_BREAK_CHAPTER_COUNT);
		this.twoLevelChapterTitle = SettingOption.getString(EnumConfigKey.TWO_LEVEL_CHAPTER_TITLE,
				Constant.DEFAULT_TWO_LEVEL_CHAPTER_TITLE);
		this.isUseTwoLevelForTOC = SettingOption.getBoolean(EnumConfigKey.IS_USE_2_LEVEL_FOR_TOC, false);

		if (this.isUseTwoLevelForTOC) {
			// reset to un-use after use
			Config.put(EnumConfigKey.IS_USE_2_LEVEL_FOR_TOC, true);
		}
		try {
			tempFileName = Paths.get(fileName).toFile().getName();
			// save extension
			if (tempFileName.contains(".txt")) {
				extension = ".txt";
			} else if (tempFileName.contains(".html")) {
				extension = ".html";
			} else if (tempFileName.contains(".epub")) {
				extension = ".epub";
			}

		} catch (Exception e1) {
			txtLog.append(String.format(Messages.getGlobalString("error.fileNameInvalid"), e1.getMessage()));
		}

		btnCancel.setEnabled(true);
		btnDownload.setEnabled(false);

		count = 0;
		storyTitle = "";

		listChapter = new ArrayList<>();
		mutilThread = new ArrayList<>();
		if (txtUrl.length() < 1000 || config != null) {
			URL u;
			try {
				if (config == null) {
					// Case auto, does not pass pageConfig into thread, need
					// retrieve from host name
					u = new URL(txtUrl);

					if (Config.isSupportHost(u.getHost()) == 1) {
						this.p = Config.getHostConfigByPageCode(u.getHost());
						config = this.p;
					}
				}
				if (isDivideFile) {
					fileNameWithoutExtension = tempFileName.replaceAll(".txt", "").replaceAll(".html", "");
					folderMutilFilePath = Paths.get(fileName).toFile().getParent() + "\\" + fileNameWithoutExtension
							+ "_GHFU_" + String.valueOf(new Date().getTime());
					File f = new File(folderMutilFilePath);
					if (!f.exists()) {
						f.mkdir();
					}
				}
			} catch (IOException e) {
				log.append(String.format(Messages.getGlobalString("error.errorMessage"), e.getMessage()));
				log.setCaretPosition(log.getDocument().getLength());
				e.printStackTrace();
			}
		}
	}

	public void cancel() {
		if (task != null) {
			for (MutilDownload md : mutilThread) {
				md.cancel();
			}
			task.checkAccess();
			task.interrupt();
			task = null;
			lblStatus.setText(Messages.getGlobalString("lblStatus.stop"));

			btnCancel.setEnabled(false);
			btnDownload.setEnabled(true);
		}
	}

	/**
	 * Check that work are done or not., synchronized method
	 */
	public void checkFinish() {
		synchronized (lockO) {
			if (!isFinish && count >= size) {
				isFinish = true;
				try {
					// Has error occur when saving
					Boolean isError = false;
					Thread.sleep(500);
					CommonUILog.info(String.format(Messages.getGlobalString("txtLog.downloadCompletedStartWriteFile")));

					progressBar.setValue(100);
					// not divide to mutilfile then
					if (!isDivideFile) {
						isError = writeConcatenateFile(isError);
					}

					lblStatus.setText(Messages.getGlobalString("lblStatus.stop"));
					// reenable button
					btnCancel.setEnabled(false);
					btnDownload.setEnabled(true);
					if (!isError) {
						// if good
						if (!CommonExceptionHandle.IsHasException) {
							CommonUILog.info(String.format(Messages.getGlobalString("txtLog.writeCompleted")));
							JOptionPane.showMessageDialog(null,
									String.format(Messages.getGlobalString("notify.downloadCompleted")));

							if (DownloadFailedCount > 0) {
								Boolean isShow = SettingOption.getBoolean(EnumConfigKey.SHOW_TIPS_ON_DOWNLOAD_FAILED,
										true);

								if (isShow) {
									new JShowHelpDialog(EnumConfigKey.SHOW_TIPS_ON_DOWNLOAD_FAILED,
											Messages.getGlobalString("help.downLoadFailed.content"),
											Messages.getGlobalString("help.downLoadFailed.tilte"));
								}
							}

						} else {
							CommonUILog.error(String.format(Messages.getGlobalString("txtLog.downloadGotAnError")));
						}

					} else {
						CommonUILog.error(Messages.getGlobalString("error.hasErrorWhenWrite"));
					}

				} catch (IOException | InterruptedException e) {
					CommonUILog.error(String.format(Messages.getGlobalString("error.errorMessage"), e.getMessage()));
					e.printStackTrace();
					btnResume.setEnabled(true);
					CommonExceptionHandle.HandleException(e, Messages.getGlobalString("error.occurWhenWrittingFile"));
				}
			}
		}
	}

	/**
	 * write content file
	 * 
	 * @param isError
	 * @return
	 * @throws UnsupportedEncodingException
	 * @throws FileNotFoundException
	 * @throws IOException
	 */
	public Boolean writeConcatenateFile(Boolean isError)
			throws UnsupportedEncodingException, FileNotFoundException, IOException {
		BufferedWriter writter;
		writter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(fileName), encoding));

		// concate file.
		Path dir = Paths.get(storyTempFolder);
		BufferedReader br = null;
		if (extension == ".html") {
			isError = saveHtmlFile(writter, dir, br);
		} else if (extension == ".txt") {
			isError = saveTextFile(writter, dir, br);
		} else if (extension == ".epub") {
			isError = saveTextFile(writter, dir, br);
		}
		return isError;
	}

	/*
	 * save html file
	 */
	public Boolean saveHtmlFile(BufferedWriter writter, Path dir, BufferedReader br) {
		Boolean firstTime = true;
		Boolean isError = false;
		try {
			// open html
			writter.write(CommonValue.getHtmlOpenString(storyTitle));
			if (ebookInfo != null && !ebookInfo.isEmpty()) {
				writter.write(CommonValue.getAnchorIDandTitle(-1, Messages.getGlobalString("text.ebookInfo")));
			}

			// mkbyme 2018.12.09 add feature two level TOC
			if (this.isUseTwoLevelForTOC) {
				StringBuffer buffer = new StringBuffer();
				for (int i = 0; i < this.size; i++) {
					if (CommonValue.checkIsTOCLV1RunIn(i, this.twoLevelBreakChapterCount, this.size)) {
						buffer.append(CommonValue.getAnchorIDandTitleForTOCLV1(i, this.twoLevelBreakChapterCount,
								this.twoLevelChapterTitle, false));
					}
				}
				writter.write(buffer.toString());
				writter.write("</br>-----o0o-----</br>");

			}

			DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.{html}");
			for (Path entry : stream) {

				if (firstTime) {
					if (entry.toFile().getName().startsWith("C")) {
						writter.write("<a name=\"start\"></a>");
						if (ebookInfo != null && !ebookInfo.isEmpty()) {
							writter.write(ebookInfo);
						}
						firstTime = false;
					}
				}
				br = new BufferedReader(new InputStreamReader(new FileInputStream(entry.toFile()), encoding));
				String line = "";
				while ((line = br.readLine()) != null) {
					writter.write(line);
					writter.write(Constant.LINE_BREAK);
				}
				br.close();
			}
			// close html
			writter.write(CommonValue.getHtmlCloseString());
		} catch (IOException x) {
			CommonExceptionHandle.HandleException(x, Messages.getGlobalString("error.hasErrorWhenWrite"));
			System.err.println(x);
			x.printStackTrace();
			isError = true;
		} finally {
			if (br != null) {
				try {
					br.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
			if (writter != null) {
				try {
					writter.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
		return isError;

	}

	/*
	 * save html file
	 */
	public Boolean saveTextFile(BufferedWriter writter, Path dir, BufferedReader br) {
		Boolean isError = false;
		try {
			DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.{txt}");
			for (Path entry : stream) {
				br = new BufferedReader(new InputStreamReader(new FileInputStream(entry.toFile()), encoding));
				String line = "", bakLine = "";
				while ((line = br.readLine()) != null) {
					bakLine = line;
					line = removeHtmlString(line);
					if (line != bakLine) {
						writter.write(line);
					} else {
						// not dif after remove -> this is a line of text only
						// -> add break after
						writter.write(line);
						writter.write(Constant.LINE_BREAK);
					}
				}
				br.close();
			}
		} catch (IOException x) {
			CommonExceptionHandle.HandleException(x, Messages.getGlobalString("error.hasErrorWhenWrite"));
			x.printStackTrace();
			isError = true;
		} finally {
			if (br != null) {
				try {
					br.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
			if (writter != null) {
				try {
					writter.close();
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		}
		return isError;

	}

	/**
	 * remove html string from content
	 * 
	 * @param line
	 * @return
	 */
	public String removeHtmlString(String line) {
		// line break
		line = line.replaceAll("<\\/?(?:h|br|p)[^>]*>", Constant.LINE_BREAK);
		// remove tag
		line = line.replaceAll("<[^>]*>", "");
		line = line.replace("&nbsp;", "");
		return line;
	}

	void doWork() {
		if (count == 0) {
			log.setText("");
			getListChapter();
			size = listChapter.size();
			interval = size / 100;
			if (interval == 0) {
				interval = 1;
			}
			// Show Frame to set Range.
			if (main.DownloadRange.visiable && size > 0) {

				DownloadRange dr = new DownloadRange();
				dr.spinnerStart.setModel(
						new SpinnerNumberModel(new Integer(1), new Integer(1), new Integer(size - 1), new Integer(1)));
				dr.spinnerEnd.setModel(
						new SpinnerNumberModel(new Integer(size), new Integer(1), new Integer(size), new Integer(1)));
				dr.setVisible(true);

				lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.totalChapter"), size));
				while (!main.DownloadRange.setComplete) {
					try {
						Thread.sleep(100);
					} catch (InterruptedException e) {
						e.printStackTrace();
					}
				}
				// reset to none
				main.DownloadRange.setComplete = false;
				main.DownloadRange.visiable = false;

				// check range
				if (DownloadRange.start < 0) {
					DownloadRange.start = 1;
					DownloadRange.end = size;
				}

				size = DownloadRange.end - DownloadRange.start;

				// index start from 0, but UI start from 1
				indexOfStartCut = --DownloadRange.start;
				indexOfEndCut = DownloadRange.end;
				DownloadRange.start = DownloadRange.end = 0;
			}
			generateNewMutilThread();

		} else {
			generateMutilThreadFromLogFile();
		}

		// start thread.
		for (MutilDownload thread : mutilThread) {
			thread.start();
		}
	}

	/**
	 * reconfig size of listChapter
	 * 
	 * @author mkbyme Jan 27, 2019
	 */
	private void updateListChapterSize() {
		if (indexOfEndCut > indexOfStartCut) {
			size = indexOfEndCut - indexOfStartCut;
		} else {
			indexOfEndCut = 0;
			indexOfStartCut = 0;
			size = listChapter.size();

		}
	}

	void generateMutilThreadFromLogFile() {
		mutilThread.clear();
		CommonUILog.info(String.format(Messages.getGlobalString("txtLog.resumeThread"), count, size));

		// resume, load index of thread from file

		// read last indexs
		Path dir = Paths.get(storyTempFolder);
		ArrayList<Integer> arr = new ArrayList<>();
		Boolean success = true;
		String fileContent = "";
		try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.{txt}")) {
			for (Path entry : stream) {
				if (!entry.toString().endsWith(".bak.txt")) {
					try {
						File file = entry.toFile();
						Scanner scanner = new Scanner(file);
						fileContent = scanner.nextLine();
						scanner.close();

					} catch (Exception e) {

						e.printStackTrace();
					}
					try {
						arr.add(Integer.parseInt(fileContent));
					} catch (NumberFormatException e) {
						success = false;
						e.printStackTrace();
					}
				}

			}
			if (!success) {
				arr.removeAll(arr);
				for (Path entry : stream) {
					if (entry.toString().endsWith(".bak.txt")) {
						try {
							File file = entry.toFile();
							Scanner scanner = new Scanner(file);
							fileContent = scanner.nextLine();
							scanner.close();

						} catch (Exception e) {

							e.printStackTrace();
						}
						try {
							arr.add(Integer.parseInt(fileContent));
						} catch (NumberFormatException e) {
							CommonExceptionHandle.HandleException(e,
									"Thử vào thư mục %temp% và sửa lại chỉ số INDEX.. để tải tiếp");
							e.printStackTrace();
						}
					}

				}
			}
		} catch (IOException x) {
			System.err.println(x);
		}
		int chunk = size / CommonValue.getNumThread();
		count = 0;
		for (int i = 0; i < arr.size() - 1; i++) {
			count += (arr.get(i) - i * chunk) + 1;
			mutilThread.add(new MutilDownload(arr.get(i) + 1, (i * chunk) + chunk, i, tempFileName, type, this));
		}
		// last thread.
		int lastIndex = arr.size() - 1;
		count += (arr.get(lastIndex) - lastIndex * chunk) + 1;
		mutilThread.add(new MutilDownload(arr.get(lastIndex) + 1, size, lastIndex, tempFileName, type, this));

	}

	void generateNewMutilThread() {
		try {
			// Create temp folder, gen random file
			tempFileName = Constant.TMP_PREFIX + String.valueOf(new Date().getTime()) + tempFileName;
			Path ptemp = Paths.get(System.getProperty("java.io.tmpdir"), tempFileName);

			Files.createDirectory(ptemp);

			storyTempFolder = ptemp.toString();

			updateListChapterSize();

			// gen thread
			int numThread = CommonValue.getNumThread();
			int chunk = size / numThread;
			Path pHead, pContent, pIndex;

			for (int i = 0; i < (numThread - 1); i++) {
				mutilThread.add(new MutilDownload((i * chunk) + indexOfStartCut, (i * chunk) + chunk + indexOfStartCut,
						i, tempFileName, type, this));
				// Create Temp File for each thread.
				pHead = Paths.get(storyTempFolder, "AH" + i + tempFileName);
				pContent = Paths.get(storyTempFolder, "C" + i + tempFileName);
				pIndex = Paths.get(storyTempFolder, "INDEX" + i + ".txt");
				if (!pHead.toFile().exists()) {
					Files.createFile(pHead);
				}
				if (!pContent.toFile().exists()) {
					Files.createFile(pContent);
				}
				if (!pIndex.toFile().exists()) {
					Files.createFile(pIndex);
				}
			}
			// LastThread
			mutilThread.add(new MutilDownload(((numThread - 1) * chunk) + indexOfStartCut, size + indexOfStartCut,
					(numThread - 1), tempFileName, type, this));
			pHead = Paths.get(storyTempFolder, "AH" + (numThread - 1) + tempFileName);
			pContent = Paths.get(storyTempFolder, "C" + (numThread - 1) + tempFileName);
			pIndex = Paths.get(storyTempFolder, "INDEX" + (numThread - 1) + ".txt");
			if (!pHead.toFile().exists()) {
				Files.createFile(pHead);
			}
			if (!pContent.toFile().exists()) {
				Files.createFile(pContent);
			}
			if (!pIndex.toFile().exists()) {
				Files.createFile(pIndex);
			}

		} catch (IOException e1) {
			e1.printStackTrace();
			CommonUILog.error(String.format(Messages.getGlobalString("error.errorMessage"), e1.getMessage()));
			CommonExceptionHandle.HandleException(e1, Messages.getGlobalString("error.occurWhenInitThreadDownload"));
		}
	}

	int getListChapter() {

		progressBar.setMaximum(100);
		progressBar.setValue(0);

		Document docHTML = null;
		Element listTagAUrl = null;
		int totalPageCount = 0;
		Boolean isAjax = false;
		String hostPattern = UrlHandler.getHostFromPattern(p.getCssQueryGetListChapter(), txtUrl);
		String pageingPattern = "";
		Boolean isAsoluted = p.getIsChapterLinkAsolute();

		// if config encoding already is UTF-8 then do nothing, else setup it
		if (!SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING)
				.equals(Constant.DEFAULT_ENCODING)) {
			Config.put(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING);
		}

		try {
			URL u = new URL(txtUrl);
			lblStatus.setText(Messages.getGlobalString("lblStatus.checkConnection"));
			// log for Range Download
			if (DownloadRange.visiable) {
				CommonUILog.info("\n" + String.format(Messages.getGlobalString("txtLog.logSelectDownloadRange")));
			}
			CommonUILog.info(String.format(Messages.getGlobalString("txtLog.starting")));
			// is host need using ajax
			isAjax = processAjaxSiteList(isAjax, hostPattern, p, u);

			if (!isAjax) {
				ArrayList<String> arr = new ArrayList<>();
				String cssQueryGetListChapter = p.getCssQueryGetListChapter()
						.replaceAll("\\;([\\w\\d\\\\W\\D=\\&\\;])*", "");
				if (p.getCssQueryGetListChapter().contains("{")) {
					arr = GetHtmlCss.getSpecialStringFromQuery(p.getCssQueryGetListChapter());
					cssQueryGetListChapter = cssQueryGetListChapter.substring(0, cssQueryGetListChapter.indexOf("{"));
				}

				// get Charset AutoMatic
				docHTML = RequestUtil.get(txtUrl, p);
				// update ENCONDING
				if (!docHTML.charset().name()
						.equals(SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING))) {
					Config.put(EnumConfigKey.ENCODING, docHTML.charset().name());
				}

				encoding = SettingOption.getString(EnumConfigKey.ENCODING, Constant.DEFAULT_ENCODING);

				// get listChapter on site;
				for (int i = 0; i < 10000; i++) {
					// processBar
					if (i % 100 == 0) {
						lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.leechPageIndex"), (i + 1)));
						progressBar.setValue(progressBar.getValue() + 1);
					}
					String urlTemp = txtUrl + pageingPattern + (i + 1);

					if (i == 0) {
						urlTemp = txtUrl;
					} else if (p.getPagingPattern().contains("{")) {

						urlTemp = processPagingPattern(pageingPattern, i);
					}
					// get doc by ENCODING
					// get Charset AutoMatic
					docHTML = Jsoup.parse(mkgethtml.GetHtmlCss.getHtmlStringFromURLbyCharset(urlTemp, p), encoding);

					// first only
					if (i == 0) {
						storyTitle = docHTML.title();
						if (p.getPagingPattern().contains(";")) {
							pageingPattern = p.getPagingPattern().substring(0, p.getPagingPattern().indexOf(";"));
						} else {
							pageingPattern = p.getPagingPattern();
						}

						if (p.getIsForumType()) {
							GetHtmlCsMix.getTotalPageOfForum(docHTML, urlTemp, p.getCssQueryGetListChapter(),
									p.getPagingPattern(), lblStatus, log).select("a").forEach(link -> {
										listChapter.add(link.attr("href"));
									});
							break;
						}
					}

					// Check cssGetListChapter is Normal or special
					if (p.getCssQueryGetListChapter().contains("{")) {
						listTagAUrl = GetHtmlCss.getListTagAUrlSpecialCssQuery(docHTML, cssQueryGetListChapter, arr);
					} else {
						listTagAUrl = docHTML.select(cssQueryGetListChapter).first();
					}
					// re-link, if found listTagAUrl then check
					if (listTagAUrl != null) {
						regenLinkRelativeOrAsoluted(listTagAUrl, hostPattern, isAsoluted, u);
					} else {
						// end of loop, searching chapter's link
						break;
					}

					// break if not found.
					if (i > 0) {
						if (GetHtmlCss.checkPageFound(listTagAUrl, listChapter.get(0),
								listChapter.get(listChapter.size() - 1), p)) {
							break;
						}
					}

					// remove duplicate link
					ArrayList<String> lstPageChapter = GetHtmlCss.getListChaptersOnPage(listTagAUrl);
					Boolean hasExists = lstPageChapter.removeIf(l -> {
						return listChapter.contains(l);
					});
					if (hasExists) {
						CommonUILog.info(
								String.format(Messages.getGlobalString("txtLog.hasDupplicateChapterLink"), hasExists));
					}
					listChapter.addAll(lstPageChapter);

					totalPageCount++;

					// logs
					CommonUILog.info(String.format(Messages.getGlobalString("txtLog.leechPage"), urlTemp));
					docHTML.childNodes().stream().close();

					lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.leechCompleted"),
							totalPageCount, totalPageCount));
					CommonUILog.info(lblStatus.getText());
				}
			}
			progressBar.setValue(0);
			// size
			size = listChapter.size();

			// Revert List
			revertChapterList();
		} catch (Exception e) {
			CommonUILog.error(String.format(Messages.getGlobalString("error.errorMessage"), e.getMessage()));
			return -1;
		}
		return 0;

	}

	/**
	 * process special host need use ajax to get content
	 * 
	 * @param isAjax
	 * @param hostPattern
	 * @param pageConfig
	 * @param u
	 * @return
	 * @throws IOException
	 */
	public Boolean processAjaxSiteList(Boolean isAjax, String hostPattern, PageConfig pageConfig, URL u)
			throws IOException {
		Boolean isAsoluted = pageConfig.getIsChapterLinkAsolute();
		switch (p.getPageCode().toLowerCase()) {
		case "truyencv.com":
			listChapter.addAll(GetHtmlCsMix.getListChaptersOnPageTruyenCV(txtUrl, p));
			isAjax = true;
			break;
		case "wikidich.com":
			listChapter.addAll(GetHtmlCsMix.getListChaptersOnPageWikiDich(txtUrl, p));
			regenLinkRelativeOrAsoluted(listChapter, hostPattern, isAsoluted, u);
			isAjax = true;
			break;
		case "truyen.tangthuvien.vn":
			listChapter.addAll(GetHtmlCsMix.getListChaptersOnPageTruyenTangThuVien(txtUrl, p));
			regenLinkRelativeOrAsoluted(listChapter, hostPattern, isAsoluted, u);
			isAjax = true;
			break;
		case "tangthucac.com":
			listChapter.addAll(GetHtmlCsMix.getListChaptersOnPageTangThuCacDotCom(txtUrl, p));
			regenLinkRelativeOrAsoluted(listChapter, hostPattern, isAsoluted, u);
			isAjax = true;
			break;

		case "truyendich.org":
			listChapter.addAll(GetHtmlCsMix.getListChaptersOnPageTruyenDichDotOrg(txtUrl, p));
			regenLinkRelativeOrAsoluted(listChapter, hostPattern, isAsoluted, u);
			isAjax = true;
			break;

		default:
			break;
		}
		return isAjax;
	}

	/**
	 * revert chapter list
	 */
	public void revertChapterList() {
		if (p.getIsRevertChapterList()) {
			int i = size - 1;
			int j = 0;
			while (i >= j) {
				String temp = listChapter.get(i);
				listChapter.set(i, listChapter.get(j));
				listChapter.set(j, temp);
				i--;
				j++;
			}

		}
	}

	/**
	 * proccess paging pattern
	 * 
	 * @param pageingPattern
	 * @param i
	 * @return
	 */
	public String processPagingPattern(String pageingPattern, int i) {
		String urlTemp;
		if (pageingPattern.contains("-")) {
			urlTemp = UrlHandler.getPagePatternUrl(p.getPagingPattern(), txtUrl,
					pageingPattern.replaceFirst("\\{[\\w\\W]*\\}", String.valueOf(i)));
		} else {
			urlTemp = UrlHandler.getPagePatternUrl(p.getPagingPattern(), txtUrl,
					pageingPattern.replaceFirst("\\{\\w*\\}", String.valueOf(i + 1)));
		}
		return urlTemp;
	}

	/*
	 * regen link string
	 */
	public void regenLinkRelativeOrAsoluted(ArrayList<String> listChapter, String hostPattern, Boolean isAsoluted,
			URL u) {
		if (!isAsoluted) {
			String cssListChapterTemp = p.getCssQueryGetListChapter();
			for (int i = 0; i < listChapter.size(); i++) {
				String link = listChapter.get(i);
				String newLink = "";
				if (cssListChapterTemp.contains(";")) {
					newLink = UrlHandler.normalizeHostAndPath(hostPattern, link, u.toString());
				} else {
					newLink = UrlHandler.normalizeHostAndPath(u.getHost(), link, u.toString());
				}
				listChapter.set(i, newLink);
				// System.out.println(newLink);
			}

		} else {
			for (int i = 0; i < listChapter.size(); i++) {
				listChapter.set(i, listChapter.get(i));
			}
		}

	}

	/**
	 * regen link from aTag
	 * 
	 * @param listTagAUrl
	 * @param hostPattern
	 * @param isAsoluted
	 * @param u
	 */
	private void regenLinkRelativeOrAsoluted(Element listTagAUrl, String hostPattern, Boolean isAsoluted, URL u) {
		if (!isAsoluted) {
			String cssListChapterTemp = p.getCssQueryGetListChapter();
			listTagAUrl.select("a").iterator().forEachRemaining((link) -> {
				String newLink = "";
				if (cssListChapterTemp.contains(";")) {
					newLink = UrlHandler.normalizeHostAndPath(hostPattern, link.attr("href"), u.toString());
				} else {
					newLink = UrlHandler.normalizeHostAndPath(u.getHost(), link.attr("href"), u.toString());
				}
				link.attr("href", newLink);
			});
		} else {
			listTagAUrl.select("a").iterator().forEachRemaining((link) -> {
				link.attr("href", UrlHandler.normalizeHost(link.attr("href")));
			});
		}
	}

	@Override
	public void run() {
		btnCancel.setEnabled(true);
		btnDownload.setEnabled(false);
		btnResume.setEnabled(false);
		doWork();
	}

	void saveDownloadFile() {

	}

	public void start() {
		task = new Thread(this, "Dowork");
		task.start();
	}

	/**
	 * update Form UI from thread
	 * 
	 * @param chapterIndex
	 * @param chapterTitle
	 */
	public void updateUICount(String chapterTitle, int threadID, int index) {
		synchronized (lockO) {
			lblStatus.setText(String.format(Messages.getGlobalString("lblStatus.downloading"), (count + 1), size,
					(chapterTitle.length() < 50 ? chapterTitle : chapterTitle.substring(0, 50) + "...")));
			if (count % interval == 0) {
				progressBar.setValue((int) ((float) count / size * 100));
			}
			count++;
		}
	}

	/**
	 * when a website using google capcha to block mutil download, this will
	 * open and you need to input captcha do continue download
	 * 
	 * @param chapter
	 *            - chapter has detected google captcha
	 * @param chapterIndex
	 *            - chapter index
	 * @param cssChapterTitle
	 *            - css query get chapter title
	 * @param cssChapterContent
	 *            - css query get chapter content
	 * @param cssRemoveContent
	 *            - css query remove unneeeded content
	 * @param isEnableChapterSign
	 *            - enable chapter site or not
	 * @return chapter was renew from valid page
	 */
	public Chapter checkGoogleRecapcha(Chapter chapter, int chapterIndex, PageConfig pageConfig) {
		Chapter c = null;
		synchronized (lockO) {
			Boolean bIsStopDownload = false;
			// has capcha -> do it then go back to continue download
			if (chapter.getIsHasCapchaBlock() && !isDoneCapcha && !isShowDoCapchaDiaglog) {
				this.isShowDoCapchaDiaglog = true;
				// show notify
				int confirm = JOptionPane.showOptionDialog(null, Messages.getGlobalString("message.robotDetectFix"),
						Messages.getGlobalString("title.notice"), JOptionPane.YES_NO_OPTION,
						JOptionPane.QUESTION_MESSAGE, null,
						new String[] { Messages.getGlobalString("btn.doCapcha"),
								Messages.getGlobalString("btn.stopDownload") },
						Messages.getGlobalString("btn.doCapcha"));

				if (confirm == JOptionPane.YES_OPTION) {
					// open web
					try {
						java.awt.Desktop.getDesktop().browse(new URI(listChapter.get(chapterIndex)));

						// show confirm
						confirm = JOptionPane.showOptionDialog(null, Messages.getGlobalString("message.doneRecapcha"),
								Messages.getGlobalString("title.notice"), JOptionPane.YES_NO_OPTION,
								JOptionPane.QUESTION_MESSAGE, null,
								new String[] { Messages.getGlobalString("btn.done"),
										Messages.getGlobalString("btn.stopDownload") },
								Messages.getGlobalString("btn.done"));

						// if done capcha
						if (confirm == JOptionPane.YES_OPTION) {
							this.isDoneCapcha = true;
							// re-get chapter has been detect that's
							// robot
							c = GetHtmlCss.getChapterTitleAndContent(chapterIndex, listChapter.get(chapterIndex), p);
							lockO.notifyAll();
						} else {
							bIsStopDownload = true;
						}
					} catch (IOException e) {
						e.printStackTrace();
						bIsStopDownload = true;
					} catch (URISyntaxException e) {
						e.printStackTrace();
						bIsStopDownload = true;
					}

				} else {
					bIsStopDownload = true;
				}
				// cancel downloading
				if (bIsStopDownload) {
					cancel();
				}
			} else {
				// if has thread that open link to user input captcha and not
				// stop download then wait this thread
				try {
					if (!this.isDoneCapcha && !bIsStopDownload) {
						lockO.wait();
					} else {
						if (bIsStopDownload) {
							cancel();
						} else {
							c = GetHtmlCss.getChapterTitleAndContent(chapterIndex, listChapter.get(chapterIndex),
									pageConfig);
						}

					}
				} catch (InterruptedException | IOException e) {
					e.printStackTrace();
				}
			}
		}

		return c;
	}
}
