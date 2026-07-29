package thread;

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.RandomAccessFile;
import java.nio.charset.Charset;
import java.nio.file.Path;
import java.nio.file.Paths;

import common.CommonValue;
import log.CommonLog;
import log.CommonUILog;
import mk.constant.Constant;
import mkgethtml.GetHtmlCss;
import models.Chapter;
import models.PageConfig;

/**
 * @author Adminz
 *
 */
public class MutilDownload implements Runnable {

	int start;
	int end;
	int type;
	int threadID;
	String fileName;
	Thread t = null;
	Path pHead, pContent, pIndex, pSingle, pIndexBak;
	OutputStreamWriter oswHead = null, oswContent = null, oswSingle = null;
	RandomAccessFile ranIndex = null, ranIndexBak = null;
	TAuto tAuto;
	/**
	 * object hold thread
	 */
	final Object lockO = new Object();

	/**
	 * init multil download
	 * 
	 * @param start
	 *            - start index
	 * @param end
	 *            - end index
	 * @param theadId
	 *            - id of thread
	 * @param fileName
	 *            - filed name
	 * @param type
	 *            - 1:auto , 0 - manual
	 * @param tAuto
	 *            - Manager Class hold this thread
	 * @author mkbyme Jan 27, 2019
	 */
	public MutilDownload(int start, int end, int theadId, String fileName, int type, TAuto tAuto) {
		this.start = start;
		this.end = end;
		this.fileName = fileName;
		this.type = type;// 1 auto ; 0 - manual
		this.threadID = theadId;
		this.tAuto = tAuto;
		t = new Thread(this);

		pHead = Paths.get(tAuto.storyTempFolder, "AH" + threadID + fileName);
		pContent = Paths.get(tAuto.storyTempFolder, "C" + threadID + fileName);
		pIndex = Paths.get(tAuto.storyTempFolder, "INDEX" + threadID + ".txt");
		pIndexBak = Paths.get(tAuto.storyTempFolder, "INDEX" + threadID + ".bak.txt");
		try {
			// not divide file
			if (!tAuto.isDivideFile) {
				oswHead = new OutputStreamWriter(new FileOutputStream(pHead.toString(), true),
						Charset.forName(tAuto.encoding));
				oswContent = new OutputStreamWriter(new FileOutputStream(pContent.toString(), true),
						Charset.forName(tAuto.encoding));

				ranIndex = new RandomAccessFile(pIndex.toFile(), "rw");
				ranIndexBak = new RandomAccessFile(pIndexBak.toFile(), "rw");
			} else {
				// folder path divide single file
				pSingle = Paths.get(tAuto.folderMutilFilePath);
			}
		} catch (IOException e) {
			e.printStackTrace();
		}

	}

	/**
	 * pause or stop thread.
	 */
	public void cancel() {
		if (t != null) {
			t.checkAccess();
			t.interrupt();
			t = null;
			try {
				if (ranIndex != null) {
					ranIndex.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (ranIndexBak != null) {
					ranIndexBak.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswHead != null) {
					oswHead.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswContent != null) {
					oswContent.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswSingle != null) {
					oswSingle.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}

		}
	}

	@Override
	public void run() {

		Boolean isForumType = tAuto.p.getIsForumType();
		PageConfig pageConfig = tAuto.p;
		String pageCode = tAuto.p.getPageCode().toLowerCase();
		try {
			for (int i = start; i < end; i++) {
				Chapter c = new Chapter();
				if (pageCode.equals("truyencv.com")) {
					c = GetHtmlCss.getChapterTitleAndContent(i, tAuto.listChapter.get(i), pageConfig);
					// if need to do input capcha
					if (c.getIsHasCapchaBlock()) {
						// if before that is done and got RECAPTCHA then set
						// flags to false and call
						if (tAuto.isDoneCapcha) {
							tAuto.isDoneCapcha = false;
							tAuto.isShowDoCapchaDiaglog = false;
						}
						Chapter check = tAuto.checkGoogleRecapcha(c, i, pageConfig);
						Thread.sleep(200);
						if (check != null) {
							c = check;
						}
					}

				} else {
					c = GetHtmlCss.getChapterTitleAndContent(i, tAuto.listChapter.get(i), pageConfig);
				}

				if (!tAuto.isDivideFile) {

					if (!c.getTitle().isEmpty()) {
						String tocLv1Body = "";
						// mkbyme 2018/12/09 - add featur 2 level for TOC
						if (tAuto.isUseTwoLevelForTOC
								&& CommonValue.checkIsTOCLV1RunIn(i, tAuto.twoLevelBreakChapterCount, tAuto.size)) {
							int breakCount = (tAuto.size - i < tAuto.twoLevelBreakChapterCount) ? (tAuto.size - i)
									: tAuto.twoLevelBreakChapterCount;
							tocLv1Body = CommonValue.getAnchorIDandTitleForTOCLV1(i, breakCount,
									tAuto.twoLevelChapterTitle, true);
						}

						if (isForumType) {
							oswHead.write(c.getTitle());
						} else {
							oswHead.write(tocLv1Body);
							oswHead.write(CommonValue.getAnchorIDandTitle(i, c.getTitle()));
						}
					}
					oswContent.write(c.getContent());
					if (i > -1) {
						String value = String.valueOf(i);
						ranIndex.setLength(0);
						ranIndex.writeBytes(value);
						ranIndexBak.setLength(0);
						ranIndexBak.writeBytes(value);
					}
				} else {
					// write single file
					Path saveSingle = Paths.get(tAuto.folderMutilFilePath,
							tAuto.fileNameWithoutExtension + "-" + String.valueOf(i + 1) + tAuto.extension);
					if (tAuto.extension == ".txt") {
						c.setTitle(tAuto.removeHtmlString(c.getTitle()));
						c.setContent(tAuto.removeHtmlString(c.getContent()));
					}
					if (!c.getContent().contains(c.getTitle())) {
						if (tAuto.extension == ".txt") {
							c.setContent(c.getTitle() + Constant.LINE_BREAK + c.getContent());
						} else {
							c.setContent(c.getTitle() + "<br/>" + c.getContent());
						}
					}
					oswSingle = new OutputStreamWriter(new FileOutputStream(saveSingle.toFile()),
							Charset.forName(tAuto.encoding));

					// text
					if (tAuto.extension == ".txt") {
						oswSingle.write(c.getContent());
					} else {
						// html
						oswSingle.write(CommonValue.getHtmlOpenString(c.getTitle() + " - " + tAuto.storyTitle));
						oswSingle.write(c.getContent());
						oswSingle.write(CommonValue.getHtmlCloseString());
					}
					oswSingle.close();
				}
				tAuto.updateUICount(c.getTitle(), threadID, i);
				Thread.sleep(CommonValue.SLEEP_TIME);

				if (c.isGetFailed) {
					// count to show help tips
					tAuto.DownloadFailedCount++;
				}
			}
		} catch (IOException | InterruptedException e) {
			CommonLog.logError(e);
			try {
				if (ranIndex != null) {
					ranIndex.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (ranIndexBak != null) {
					ranIndexBak.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswHead != null) {
					oswHead.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswContent != null) {
					oswContent.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswSingle != null) {
					oswSingle.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			e.printStackTrace();
			CommonUILog.error(e.getMessage());
		} finally {
			try {
				if (ranIndex != null) {
					ranIndex.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (ranIndexBak != null) {
					ranIndexBak.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswHead != null) {
					oswHead.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswContent != null) {
					oswContent.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			try {
				if (oswSingle != null) {
					oswSingle.close();
				}
			} catch (IOException e1) {
				e1.printStackTrace();
			}
			tAuto.checkFinish();
		}
	}

	/**
	 * Start thread
	 */
	public void start() {
		t = new Thread(this);
		t.start();
	}

}
