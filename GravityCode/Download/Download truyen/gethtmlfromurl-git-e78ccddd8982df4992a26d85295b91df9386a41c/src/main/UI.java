package main;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.GridLayout;
import java.awt.HeadlessException;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.StringSelection;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusAdapter;
import java.awt.event.FocusEvent;
import java.awt.event.InputMethodEvent;
import java.awt.event.InputMethodListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Locale;

import javax.net.ssl.SSLHandshakeException;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JProgressBar;
import javax.swing.JScrollPane;
import javax.swing.JSeparator;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.ScrollPaneConstants;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;
import javax.swing.border.CompoundBorder;
import javax.swing.border.TitledBorder;
import javax.swing.event.CaretEvent;
import javax.swing.event.CaretListener;
import javax.swing.filechooser.FileNameExtensionFilter;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonKey;
import common.CommonValue;
import common.Enumeration;
import common.Enumeration.EnumConfigKey;
import javafx.application.Platform;
import log.CommonLog;
import main.tweak.QuickLoginFromCookies;
import mk.constant.Constant;
import mkbrowser.MKBrowser;
import mkgethtml.Config;
import mkgethtml.GetHtmlCss;
import mkgethtml.SettingOption;
import models.PageConfig;
import resource.text.Messages;
import thread.TAuto;
import utils.CheckUpdate;
import utils.FileUtil;
import utils.UrlHandler;

public class UI {
	private static void addPopup(Component component, final JPopupMenu popup) {
		component.addMouseListener(new MouseAdapter() {
			@Override
			public void mousePressed(MouseEvent e) {
				if (e.isPopupTrigger()) {
					showMenu(e);
				}
			}

			@Override
			public void mouseReleased(MouseEvent e) {
				if (e.isPopupTrigger()) {
					showMenu(e);
				}
			}

			private void showMenu(MouseEvent e) {
				popup.show(e.getComponent(), e.getX(), e.getY());
			}
		});
	}

	/**
	 * Launch the application.
	 * 
	 * @throws IOException
	 */
	public static void main(String[] args) throws IOException {

		CommonValue.initValue();

		System.setProperty("file.encoding", "UTF-8");

		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				Main.window.jfrmUiGetHtml.setVisible(true);
			}
		});
	}

	public JFrame jfrmUiGetHtml;
	private JTextField txtURL;
	JComboBox<PageConfig> cboPageConfigList;
	JProgressBar progressBar;
	JLabel lblStatus;
	TAuto tAuto;
	JButton btnCancel;
	JButton btnDownload;
	JButton btnResume;
	public JTextArea txtLog;
	JPopupMenu popupMenu;
	JCheckBox chckbxAddEbookInfo;
	JCheckBox chckbxDownloadFrom;
	public JCheckBox chckbxOneFilePer;
	JButton btnHelp;
	PageConfig p;
	JComboBox<String> cboHostType;
	JMenuItem mntmLoginTo;
	/*
	 * button count host
	 */
	public JButton btnHostCount;

	CopyRightInfo cri;

	int isHelpShowHitCount = 0;

	int countChildWindow = 0;

	private JTextField txtFilter;

	/**
	 * Create the application.
	 */
	public UI() {
		initialize();

		try {
			// set User UX
			Boolean chkState = SettingOption.getBoolean(EnumConfigKey.REMEMBER_ONE_PER_FILE, false);
			chckbxOneFilePer.setSelected(chkState);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	CheckUpdate checkUpdate(Boolean isCheckOnly) throws IOException {
		CheckUpdate check = new CheckUpdate();
		if (!check.isUpdated() && !isCheckOnly) {
			Update frameUpdate = null;
			if (!check.isAppUpdated) {
				frameUpdate = new Update(
						String.format(Messages.getGlobalString("notify.updateSoftware"), CommonValue.APP_VERSION,
								check.jarName.replaceAll("[^\\.\\d]", "")),
						check.message, Messages.getGlobalString("btn.update"), Messages.getGlobalString("btn.skip"),
						check);
			} else {
				frameUpdate = new Update(Messages.getGlobalString("notify.updateNweConfigFile"), check.message,
						Messages.getGlobalString("btn.update"), Messages.getGlobalString("btn.skip"), check);

			}
			frameUpdate.frmUpdate.setVisible(true);
		}
		return check;
	}

	/**
	 * Get HTML in background Thread and logging
	 */
	void doWork() {
		// check URL protocol http or https only
		if (!txtURL.getText().toLowerCase().trim().contains("http://")
				&& !txtURL.getText().toLowerCase().trim().contains("https://")) {
			JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.linkPathMustBeStartWithHttp"));
			return;
		}

		try {
			URL u = new URL(txtURL.getText());
			// check program can serilizaber this host or not
			int checkHost = Config.isSupportHost(u.getHost());
			if (checkHost == 0) {
				JOptionPane.showMessageDialog(null,
						String.format(Messages.getGlobalString("notify.hostDoesNotSupportTryAddOne"), u.getHost()));
				return;
			}
			if (checkHost == -1) {

				if (JOptionPane.showConfirmDialog(null,
						String.format(Messages.getGlobalString("message.hostUseForManualGet"), u.getHost()),
						Messages.getGlobalString("title.notify"), JOptionPane.YES_NO_OPTION,
						JOptionPane.QUESTION_MESSAGE) == JOptionPane.YES_OPTION) {
					new ManualGetUI(u.getHost()).setVisible(true);
					return;
				}

			}
			// checking url path is former.
			String urlCheck = u.toString();
			try {
				urlCheck = GetHtmlCss.getRespondLocation(u.toString());
			} catch (SSLHandshakeException e) {
				txtLog.append(e.getMessage());
				txtLog.append("\n-----------------------------");
				txtLog.append(String.format(Messages.getGlobalString("log.certificateDoesNotExist"), u.getHost()));
				txtLog.append(String.format("log.addedNewCertificate"));
				txtLog.append("\n-----------------------------");
				txtLog.append(String.format(Messages.getGlobalString("log.restartAppToApplyChangeCert")));
				txtLog.append("\n-----------------------------");
				txtLog.setCaretPosition(txtLog.getText().length());
				return;
			} catch (IOException e) {
				txtLog.append(e.getMessage());
				e.printStackTrace();
			}

			if (!u.toString().equalsIgnoreCase(urlCheck)) {
				JOptionPane.showMessageDialog(null,
						String.format(Messages.getGlobalString("message.pathDownloadInvalid")));
				return;
			}

			JFileChooser jfc = new JFileChooser();
			FileNameExtensionFilter filter = new FileNameExtensionFilter(
					Messages.getGlobalString("file.fileExtensionHTML"), "htm", "html");
			FileNameExtensionFilter filter1 = new FileNameExtensionFilter(
					Messages.getGlobalString("file.fileExtensionTXT"), "txt");
			jfc.addChoosableFileFilter(filter);
			jfc.addChoosableFileFilter(filter1);

			jfc.setDialogTitle(Messages.getGlobalString("file.chooseSavePath"));
			try {
				// handing path -> fileName
				String fileName = u.getPath();
				if (fileName.charAt(fileName.length() - 1) == '/') {
					fileName = fileName.substring(0, fileName.length() - 1);
				}
				fileName = fileName.substring(fileName.lastIndexOf("/") + 1);

				String recentFolder = SettingOption.getString(EnumConfigKey.RECENT_FOLDER,
						Constant.DEFAULT_RECENT_FOLDER) + File.separator + fileName;
				jfc.setSelectedFile(new File(recentFolder));
			} catch (Exception e) {
				e.printStackTrace();
				jfc.setSelectedFile(new File(u.getPath()));
			}

			jfc.setFileFilter(filter);

			// check jfc button is APPROVE_OPTION
			if (jfc.showSaveDialog(null) != JFileChooser.APPROVE_OPTION) {
				return;
			}
			String path = jfc.getSelectedFile().getPath();

			if (filter.equals(jfc.getFileFilter())) {
				if (!path.toLowerCase().contains(".html")) {
					path += ".html";
				}
			} else if (filter1.equals(jfc.getFileFilter()) && !path.toLowerCase().contains(".txt")) {
				if (!path.toLowerCase().contains(".txt")) {
					path += ".txt";
				}
			} else {
				path += ".html";
			}

			// Download Options
			if (chckbxDownloadFrom.isSelected()) {
				DownloadRange.visiable = true;
				chckbxDownloadFrom.setSelected(false);
			}
			// save recent folder;
			Config.put(EnumConfigKey.RECENT_FOLDER, jfc.getSelectedFile().getParentFile().getPath());
			Config.saveConfig(Enumeration.ConfigType.Setting);

			tAuto = new TAuto(btnCancel, btnDownload, btnResume, u.toString(), path, lblStatus, txtLog, progressBar,
					cri != null ? cri.ebookInfo : "", chckbxOneFilePer.isSelected(), null);
			tAuto.start();

		} catch (MalformedURLException e) {
			JOptionPane.showMessageDialog(null, e.getMessage());
		}
	}

	void updateHostCount() {
		btnHostCount.setText(Config.getAllHostConfig().size() + " Host");
	}

	/*
	 * Load pageconfig from ghfuConfig.data to combobox with filter
	 */
	void getListToCombo(String filterChain) {
		cboPageConfigList.removeAllItems();
		filterChain = filterChain.replaceAll("(https?:\\/\\/)|(\\/.+$)", "").toLowerCase();
		int filterGroup = 0;// All
		filterGroup = cboHostType.getSelectedIndex();
		if (filterChain.length() < 3) {
			for (PageConfig pageConfig : Config.getAllHostConfig()) {
				// all
				if (filterGroup == 0) {
					cboPageConfigList.addItem(pageConfig);

				} else if (filterGroup == 1 && pageConfig.getIsVietNameseHost()) {
					// viet nam's host
					cboPageConfigList.addItem(pageConfig);
				} else if (filterGroup == 2 && !pageConfig.getIsVietNameseHost()) {
					cboPageConfigList.addItem(pageConfig);
				}
			}
		} else {
			for (PageConfig pageConfig : Config.getAllHostConfig()) {
				if (pageConfig.getPageCode().toLowerCase().contains(filterChain)) {
					// all
					if (filterGroup == 0) {
						cboPageConfigList.addItem(pageConfig);

					} else if (filterGroup == 1 && pageConfig.getIsVietNameseHost()) {
						// viet nam's host
						cboPageConfigList.addItem(pageConfig);
					} else if (filterGroup == 2) {
						cboPageConfigList.addItem(pageConfig);
					}
				}
			}
		}
		btnHostCount.setText(cboPageConfigList.getItemCount() + " Host");
	}

	/**
	 * Initialize the contents of the frame.
	 * 
	 * @wbp.parser.entryPoint
	 */
	private void initialize() {
		try {
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		} catch (Exception e3) {
			String deleleOldAppPath = SettingOption.getString(EnumConfigKey.DELETE_ON_EXIST, "");
			Config.reConfig();
			if (!deleleOldAppPath.isEmpty()) {
				Config.put(EnumConfigKey.DELETE_ON_EXIST, deleleOldAppPath.toString());
			}
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		}

		jfrmUiGetHtml = new JFrame();
		jfrmUiGetHtml.getContentPane().setForeground(Color.RED);
		jfrmUiGetHtml.getContentPane().setFocusCycleRoot(true);
		jfrmUiGetHtml.getContentPane().addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent arg0) {
				if (arg0.isPopupTrigger()) {
					popupMenu.show(arg0.getComponent(), arg0.getX(), arg0.getY());
				}
			}
		});
		jfrmUiGetHtml.addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (!btnDownload.isEnabled()) {
					int confirm = JOptionPane.showOptionDialog(null, Messages.getGlobalString("warning.inDownloading"),
							Messages.getGlobalString("title.downloading"), JOptionPane.YES_NO_OPTION,
							JOptionPane.QUESTION_MESSAGE, null,
							new String[] { Messages.getGlobalString("btn.yes"), Messages.getGlobalString("btn.no") },
							Messages.getGlobalString("btn.no"));
					if (confirm == JOptionPane.YES_OPTION) {
						Platform.exit();
						FileUtil.deleteOldFiles();
						System.exit(0);
					}

				} else {
					Platform.exit();
					FileUtil.deleteOldFiles();
					System.exit(0);
				}
			}

			@Override
			public void windowOpened(WindowEvent arg0) {
				getListToCombo("");
			}

		});
		jfrmUiGetHtml.setIconImage(Toolkit.getDefaultToolkit().getImage(UI.class.getResource("/resource/box-16.png")));
		jfrmUiGetHtml.setTitle(CommonValue.getAppName() + " - by Mkbyme");
		jfrmUiGetHtml.setBounds(100, 100, 800, 600);
		jfrmUiGetHtml.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE);

		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}

		popupMenu = new JPopupMenu();
		addPopup(jfrmUiGetHtml, popupMenu);

		JMenuItem mntmPaste = new JMenuItem(Messages.getString("UI.mntmPaste.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmPaste.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				try {
					if (Toolkit.getDefaultToolkit().getSystemClipboard().getData(DataFlavor.stringFlavor).toString()
							.length() < 2000) {
						txtURL.setText(Toolkit.getDefaultToolkit().getSystemClipboard().getData(DataFlavor.stringFlavor)
								.toString());
					}
				} catch (HeadlessException | UnsupportedFlavorException | IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		});
		mntmPaste.setIcon(new ImageIcon(UI.class.getResource("/resource/Paste-16.png")));
		popupMenu.add(mntmPaste);

		JMenuItem mntmDownload = new JMenuItem(Messages.getString("UI.mntmDownload.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmDownload.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				btnDownload.doClick();
			}
		});

		JSeparator separator_3 = new JSeparator();
		popupMenu.add(separator_3);
		mntmDownload.setIcon(new ImageIcon(UI.class.getResource("/resource/Down-16.png")));
		popupMenu.add(mntmDownload);

		JMenuBar menuBar = new JMenuBar();
		jfrmUiGetHtml.setJMenuBar(menuBar);

		JMenu mnFile = new JMenu(Messages.getString("UI.mnFile.text")); //$NON-NLS-1$ //$NON-NLS-2$
		menuBar.add(mnFile);

		JMenuItem mntmCit = new JMenuItem(Messages.getString("UI.mntmCit.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmCit.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				if (Main.pageConfigManager == null) {
					Main.pageConfigManager = new PageConfigManager();
				}
				Main.pageConfigManager.setVisible(true);
			}
		});

		JMenuItem mntmCaSMi = new JMenuItem(Messages.getString("UI.mntmCaSMi.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmCaSMi.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				try {
					// start jar with agruments (turn on checkupdate and
					// launcher)
					Runtime.getRuntime()
							.exec("java -jar " + CommonValue.getAppJARFile().getAbsolutePath() + " launcher off");
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
		});
		mntmCaSMi.setIcon(new ImageIcon(UI.class.getResource("/resource/box-16.png")));
		mnFile.add(mntmCaSMi);

		JSeparator separator_2 = new JSeparator();
		mnFile.add(separator_2);

		JMenuItem mntmOpenBrowser = new JMenuItem(Messages.getString("UI.mntmOpenBrowser.text")); //$NON-NLS-1$
		mntmOpenBrowser.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				if (Main.browser == null) {
					Main.browser = new MKBrowser();
				}
				Main.browser.setVisible(true);
				Main.browser.loadURL("https://google.com");
			}
		});
		mntmOpenBrowser.setIcon(new ImageIcon(UI.class.getResource("/resource/browser-16.png")));
		mnFile.add(mntmOpenBrowser);

		JSeparator separator_6 = new JSeparator();
		mnFile.add(separator_6);
		mntmCit.setIcon(new ImageIcon(UI.class.getResource("/resource/Dropbox Filled-16.png")));
		mnFile.add(mntmCit);

		JMenuItem mntmSetting = new JMenuItem(Messages.getString("UI.mntmSetting.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmSetting.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (Main.setting == null) {
					Main.setting = new Setting();
				}
				Main.setting.setVisible(true);
			}
		});
		mntmSetting.setIcon(new ImageIcon(UI.class.getResource("/resource/settings.png")));
		mnFile.add(mntmSetting);

		JSeparator separator_1 = new JSeparator();
		mnFile.add(separator_1);

		JMenuItem mntmMannualGet = new JMenuItem(Messages.getString("UI.mntmMannualGet.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmMannualGet.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (Main.manualGetUI == null) {
					Main.manualGetUI = new ManualGetUI();
				}
				Main.manualGetUI.setVisible(true);
			}
		});
		mntmMannualGet.setIcon(new ImageIcon(UI.class.getResource("/resource/Whole Hand-16.png")));
		mnFile.add(mntmMannualGet);

		JSeparator separator = new JSeparator();
		mnFile.add(separator);

		JMenuItem mntmThot = new JMenuItem(Messages.getString("UI.mntmThot.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmThot.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				if (!btnDownload.isEnabled()) {
					int confirm = JOptionPane.showOptionDialog(null, Messages.getGlobalString("warning.inDownloading"),
							Messages.getGlobalString("title.downloading"), JOptionPane.YES_NO_OPTION,
							JOptionPane.QUESTION_MESSAGE, null,
							new String[] { Messages.getGlobalString("btn.yes"), Messages.getGlobalString("btn.no") },
							Messages.getGlobalString("btn.no"));
					if (confirm == JOptionPane.YES_OPTION) {
						System.exit(0);
					}

				} else {
					System.exit(0);
				}
			}
		});
		mntmThot.setIcon(new ImageIcon(UI.class.getResource("/resource/log-out.png")));
		mnFile.add(mntmThot);

		JMenu mnAbout = new JMenu(Messages.getString("UI.mnAbout.text")); //$NON-NLS-1$ //$NON-NLS-2$
		menuBar.add(mnAbout);

		JMenuItem mntmTcGi = new JMenuItem(Messages.getString("UI.mntmTcGi.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmTcGi.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				JOptionPane.showMessageDialog(null, "code by Mkbyme\nemail: mkbyme@gmail.com\nfacebook: fb.com/mkbyme",
						Messages.getGlobalString("title.author"), JOptionPane.INFORMATION_MESSAGE);
			}
		});

		mntmTcGi.setIcon(new ImageIcon(UI.class.getResource("/resource/copyright.png")));
		mnAbout.add(mntmTcGi);

		JMenuItem mntmTrGip = new JMenuItem(Messages.getString("UI.mntmTrGip.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmTrGip.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				Info i = new Info();
				i.setAlwaysOnTop(true);
				i.setAutoRequestFocus(true);
				i.setVisible(true);
			}
		});
		mntmTrGip.setIcon(new ImageIcon(UI.class.getResource("/resource/information.png")));
		mnAbout.add(mntmTrGip);

		JMenuItem mntmCheckUpdate = new JMenuItem(Messages.getString("UI.mntmCheckUpdate.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmCheckUpdate.setIcon(new ImageIcon(UI.class.getResource("/resource/Available Updates-16.png")));
		mntmCheckUpdate.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				Thread t = new Thread(new Runnable() {

					@Override
					public void run() {
						CheckUpdate check = new CheckUpdate();
						try {
							check = checkUpdate(false);
							if (check.isAppUpdated & check.isConfigUpdated) {
								JOptionPane.showMessageDialog(null,
										String.format(Messages.getGlobalString("notify.wasLastestUpdateVersion"),
												check.jarName, check.fileSize,
												new SimpleDateFormat("HH:mm:ss dd/MM/yyyy").format(check.date)));
							}
						} catch (HeadlessException | IOException e) {
							e.printStackTrace();
						}

					}
				});
				t.start();
			}
		});
		mnAbout.add(mntmCheckUpdate);

		JMenuItem mntmHomePage = new JMenuItem(Messages.getString("UI.mntmHomePage.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmHomePage.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.LinkDownloadApp));
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
			}
		});

		JSeparator separator_4 = new JSeparator();
		mnAbout.add(separator_4);
		mntmHomePage.setIcon(new ImageIcon(UI.class.getResource("/resource/Home-16.png")));
		mnAbout.add(mntmHomePage);

		JMenuItem mntmFanPage = new JMenuItem(Messages.getString("UI.mntmFanPage.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmFanPage.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e2) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.LinkFanPage));
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
			}
		});
		mntmFanPage.setIcon(new ImageIcon(UI.class.getResource("/resource/Facebook-16.png")));
		mnAbout.add(mntmFanPage);

		JMenu mnHelpLink = new JMenu(Messages.getString("UI.mnHelpLink.text")); //$NON-NLS-1$ //$NON-NLS-2$
		menuBar.add(mnHelpLink);

		JMenuItem mntmHowToUse = new JMenuItem(Messages.getString("UI.mntmHowToUse.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmHowToUse.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkHowToUse));
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
			}
		});
		mntmHowToUse.setIcon(new ImageIcon(UI.class.getResource("/resource/box-16.png")));
		mnHelpLink.add(mntmHowToUse);

		JMenuItem mntmHowToConvert = new JMenuItem(Messages.getString("UI.mntmHowToConvert.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmHowToConvert.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e1) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkHowToConvert));
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
			}
		});
		mntmHowToConvert.setIcon(new ImageIcon(UI.class.getResource("/resource/help-desk-icon.png")));
		mnHelpLink.add(mntmHowToConvert);

		JMenuItem mntmHowToAdd = new JMenuItem(Messages.getString("UI.mntmHowToAdd.text")); //$NON-NLS-1$ //$NON-NLS-2$
		mntmHowToAdd.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e1) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkAddHost));
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
			}
		});
		mntmHowToAdd.setIcon(new ImageIcon(UI.class.getResource("/resource/Whole Hand-16.png")));
		mnHelpLink.add(mntmHowToAdd);

		JSeparator separator_5 = new JSeparator();
		mnHelpLink.add(separator_5);

		JMenuItem menuItem = new JMenuItem(Messages.getString("UI.menuItem.text_1")); //$NON-NLS-1$ //$NON-NLS-2$
		menuItem.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				CheckUpdate check = new CheckUpdate();
				check.isAppUpdated = true;
				check.isConfigUpdated = false;
				check.jarName = CommonValue.getAppJARFile().getName();
				check.setFileDownloadLink(CommonValue.getDownloadLinkConfigFile());
				Update frameUpdate = new Update(Messages.getGlobalString("title.downloadConfigFile"),
						Messages.getGlobalString("message.downloadConfigFile"),
						Messages.getGlobalString("btn.download"), Messages.getGlobalString("btn.skip"), check);
				frameUpdate.frmUpdate.setVisible(true);
			}
		});
		menuItem.setIcon(new ImageIcon(UI.class.getResource("/resource/Dropbox Filled-16.png")));
		mnHelpLink.add(menuItem);

		JMenu mnTweak = new JMenu(Messages.getString("UI.mnTweak.text")); //$NON-NLS-1$
		menuBar.add(mnTweak);

		mntmLoginTo = new JMenuItem(Messages.getString("UI.mntmLoginto.text")); //$NON-NLS-1$
		mntmLoginTo.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				// login menu action
				if (Main.browser == null) {
					Main.browser = new MKBrowser();
				}
				cboPageConfigList.getSelectedItem();
				Main.browser.setVisible(true);
				p = (PageConfig) cboPageConfigList.getSelectedItem();
				String url = "https://google.com";
				String pageCode = "google.com";
				if (p != null) {
					pageCode = p.getPageCode();
					url = UrlHandler.normalizeHost(pageCode);
				}
				// load and save pageCode -> to save LoginInfo for later
				Main.browser.loadURL(url, pageCode);
			}
		});
		mntmLoginTo.setIcon(new ImageIcon(UI.class.getResource("/resource/login-icon-16.png")));
		mnTweak.add(mntmLoginTo);

		JMenuItem mntmQuickLoginFrom = new JMenuItem(Messages.getString("UI.mntmQuickLoginFrom.text")); //$NON-NLS-1$
		mntmQuickLoginFrom.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				// open quick login from cookies
				if (Main.quickLogin == null) {
					Main.quickLogin = new QuickLoginFromCookies();
				}
				Main.quickLogin.setVisible(true);
				try {
					p = (PageConfig) cboPageConfigList.getSelectedItem();
					if (p != null) {
						Main.quickLogin.setSelectionPage(p);
					}
				} catch (Exception e1) {
					CommonLog.logError(e1);
					e1.printStackTrace();
				}

			}
		});
		mntmQuickLoginFrom.setIcon(new ImageIcon(UI.class.getResource("/resource/cookies-16.png")));
		mnTweak.add(mntmQuickLoginFrom);

		JLabel lblUrl = new JLabel(Messages.getString("UI.lblUrl.text")); //$NON-NLS-1$ //$NON-NLS-2$

		txtURL = new JTextField();
		txtURL.addCaretListener(new CaretListener() {
			@Override
			public void caretUpdate(CaretEvent arg0) {
				if (!txtURL.getText().equals(Messages.getString("UI.txtURL.text"))) {
					txtURL.setForeground(Color.BLACK);
				}
			}
		});

		txtURL.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent arg0) {
				if (txtURL.getText().equals(Messages.getString("UI.txtURL.text"))) {
					txtURL.setText("");
					txtURL.setForeground(Color.BLACK);
				}
			}

			@Override
			public void focusLost(FocusEvent e) {
				if (txtURL.getText().isEmpty()) {
					txtURL.setText(Messages.getString("UI.txtURL.text"));
					txtURL.setForeground(Color.GRAY);
				}
			}

		});
		txtURL.setText(Messages.getString("UI.txtURL.text")); //$NON-NLS-1$ //$NON-NLS-2$
		txtURL.setForeground(Color.GRAY);
		txtURL.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent arg0) {
				if (arg0.isPopupTrigger()) {
					popupMenu.show(arg0.getComponent(), arg0.getX(), arg0.getY());
				}
			}
		});

		txtURL.setColumns(10);

		btnDownload = new JButton(Messages.getString("UI.btnDownload.text")); //$NON-NLS-1$ //$NON-NLS-2$
		btnDownload.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				doWork();
			}
		});

		cboPageConfigList = new JComboBox<>();
		cboPageConfigList.setFont(new Font("Tahoma", Font.PLAIN, 13));
		cboPageConfigList.setBorder(null);
		cboPageConfigList.addItemListener(new ItemListener() {
			@Override
			public void itemStateChanged(ItemEvent arg0) {
				// update text guid and login
				p = (PageConfig) cboPageConfigList.getSelectedItem();
				if (p != null) {
					btnHelp.setText(Messages.getString("UI.btnHelp.text") + "\"" + p.getPageCode() + "\"");
					mntmLoginTo
							.setText(String.format(Messages.getString("UI.mntmLoginto.textFormat"), p.getPageCode()));
				}
			}
		});

		btnCancel = new JButton(Messages.getString("UI.btnCancel.text")); //$NON-NLS-1$ //$NON-NLS-2$
		btnCancel.setEnabled(false);
		btnCancel.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				tAuto.cancel();
				btnResume.setEnabled(true);
			}
		});

		btnResume = new JButton(Messages.getString("UI.btnResume.text"));
		btnResume.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				tAuto.start();
				btnResume.setEnabled(false);
			}
		});
		btnResume.setEnabled(false);

		btnHelp = new JButton(Messages.getString("UI.btnHelp.text"));
		btnHelp.setHorizontalAlignment(SwingConstants.LEFT);
		btnHelp.setHorizontalTextPosition(SwingConstants.RIGHT);
		btnHelp.setAutoscrolls(true);
		btnHelp.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent arg0) {
				if (p != null && !p.getIsManualGet() && arg0.isPopupTrigger()) {
					popupMenu.show(arg0.getComponent(), arg0.getX(), arg0.getY());
				}
			}
		});
		btnHelp.setContentAreaFilled(false);
		btnHelp.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {

				if (p.getIsManualGet()) {
					JOptionPane.showMessageDialog(null,
							String.format(Messages.getGlobalString("message.hostUseForManualGet"), p.getPageCode()),
							Messages.getGlobalString("title.notify"), JOptionPane.INFORMATION_MESSAGE);
					// show open manual get UI
					new ManualGetUI(p.getPageCode()).setVisible(true);

				} else {

					int buttonOption = JOptionPane.YES_NO_OPTION;
					String options[] = new String[] { Messages.getGlobalString("btn.copyLinkDemo"),
							Messages.getGlobalString("btn.close") };

					if (!p.getScriptJS().trim().isEmpty()) {
						options = new String[] { Messages.getGlobalString("btn.copyLinkDemo"),
								Messages.getGlobalString("btn.copyScript"), Messages.getGlobalString("btn.close") };
						buttonOption = JOptionPane.YES_NO_CANCEL_OPTION;
					}
					int result = JOptionPane.showOptionDialog(null, p.getTextGuide(),
							Messages.getGlobalString("title.help"), buttonOption, JOptionPane.INFORMATION_MESSAGE, null,
							options, options[0]);
					Clipboard c = Toolkit.getDefaultToolkit().getSystemClipboard();
					if (result == JOptionPane.YES_OPTION) {

						c.setContents(new StringSelection(p.getUrlPageTest()), null);
					} else if (result == JOptionPane.NO_OPTION) {
						c.setContents(new StringSelection(p.getScriptJS()), null);
					}
				}
			}
		});
		btnHelp.setIcon(new ImageIcon(UI.class.getResource("/resource/help-desk-icon.png")));
		jfrmUiGetHtml.getContentPane()
				.setLayout(new FormLayout(new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC,
						ColumnSpec.decode("99px"), FormSpecs.LABEL_COMPONENT_GAP_COLSPEC,
						ColumnSpec.decode("319px:grow"), FormSpecs.LABEL_COMPONENT_GAP_COLSPEC,
						ColumnSpec.decode("110px"), FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
						new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
								FormSpecs.UNRELATED_GAP_ROWSPEC, RowSpec.decode("24px"), RowSpec.decode("30px"),
								FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("25px"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("top:74px:grow"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("24px"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("155px:grow"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		JLabel lblFilterHost = new JLabel(Messages.getString("UI.lblFilterHost.text")); //$NON-NLS-1$ //$NON-NLS-2$
		jfrmUiGetHtml.getContentPane().add(lblFilterHost, "2, 4, right, fill");

		JPanel panel_2 = new JPanel();
		panel_2.setAlignmentY(0.0f);
		panel_2.setAlignmentX(0.0f);
		jfrmUiGetHtml.getContentPane().add(panel_2, "4, 4, fill, center");
		panel_2.setLayout(
				new FormLayout(
						new ColumnSpec[] { ColumnSpec.decode("left:max(60dlu;default)"),
								ColumnSpec.decode("122px:grow"), ColumnSpec.decode("16dlu"), },
						new RowSpec[] { RowSpec.decode("24px"), }));

		cboHostType = new JComboBox<String>();
		cboHostType.addItem(Messages.getGlobalString("const.hostType.All"));
		cboHostType.addItem(Messages.getGlobalString("const.hostType.vietnam"));
		cboHostType.addItem(Messages.getGlobalString("const.hostType.International"));
		cboHostType.setSelectedIndex(0);
		cboHostType.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent arg0) {
				getListToCombo("");
			}
		});
		panel_2.add(cboHostType, "1, 1, fill, fill");

		txtFilter = new JTextField();
		panel_2.add(txtFilter, "2, 1, fill, fill");
		txtFilter.addInputMethodListener(new InputMethodListener() {
			@Override
			public void caretPositionChanged(InputMethodEvent arg0) {
				if (txtFilter.getText().isEmpty() && !txtFilter.isFocusOwner()) {
					txtFilter.setText(Messages.getString("UI.txtFilter.text"));
					txtFilter.setForeground(Color.GRAY);
				}
			}

			@Override
			public void inputMethodTextChanged(InputMethodEvent arg0) {
			}
		});
		txtFilter.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				getListToCombo(txtFilter.getText());
				// if length >= 3 and key == Enter show form help
				if (txtFilter.getText().length() > 2 && arg0.getKeyCode() == '\n' && isHelpShowHitCount == 0) {
					isHelpShowHitCount++;
					btnHelp.doClick();
				} else if (isHelpShowHitCount > 0) {
					isHelpShowHitCount--;
					txtFilter.requestFocus(false);
					txtURL.requestFocus();

				}
			}
		});
		txtFilter.setForeground(Color.GRAY);
		txtFilter.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent arg0) {
				if (txtFilter.getText().equals(Messages.getString("UI.txtFilter.text"))) {
					txtFilter.setText("");
					txtFilter.setForeground(Color.BLACK);
				}
			}

			@Override
			public void focusLost(FocusEvent e) {
				if (txtFilter.getText().isEmpty()) {
					txtFilter.setText(Messages.getString("UI.txtFilter.text"));
					txtFilter.setForeground(Color.GRAY);
				}
			}
		});

		txtFilter.setText(Messages.getString("UI.txtFilter.text"));
		txtFilter.setColumns(10);
		JButton btnX = new JButton("");
		btnX.setToolTipText(Messages.getString("UI.btnX.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		panel_2.add(btnX, "3, 1, left, top");
		btnX.setInheritsPopupMenu(true);
		btnX.setDefaultCapable(false);
		btnX.setSelectedIcon(new ImageIcon(UI.class.getResource("/resource/Delete-16-hover.png")));
		btnX.setIcon(new ImageIcon(UI.class.getResource("/resource/Delete-16.png")));
		btnX.setPreferredSize(new Dimension(45, 24));
		btnX.setMargin(new Insets(0, 0, 0, 0));
		btnX.setForeground(Color.GRAY);
		btnX.setBorder(new CompoundBorder());
		btnX.setBackground(SystemColor.control);
		btnX.setFocusable(false);
		btnX.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				txtFilter.setText("");
				getListToCombo("");
			}
		});

		btnHostCount = new JButton(Messages.getString("UI.btnBtnhostcount.text")); //$NON-NLS-1$
		btnHostCount.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				String message = Messages.getString("UI.hostInfoMessage");
				int totalHost = Config.getAllHostConfig().size();
				int countList[] = new int[4];
				countList[0] = 0;
				countList[1] = 0;
				countList[2] = 0;
				countList[3] = 0;// host việt
				Config.getAllHostConfig().forEach(a -> {
					if (a.getIsManualGet()) {
						countList[1]++;
					} else if (a.getIsForumType()) {
						countList[2]++;
					} else if (a.getIsVietNameseHost()) {
						countList[3]++;// host việt
					} else {
						countList[0]++;
					}
				});
				message = String.format(message, countList[0], countList[1], countList[2], countList[3], totalHost);
				JOptionPane.showMessageDialog(null, message, Messages.getString("UI.hostInfoMesageTitle"),
						JOptionPane.INFORMATION_MESSAGE);
			}
		});
		btnHostCount.setFont(new Font("Tahoma", Font.BOLD, 13));
		btnHostCount.setToolTipText(Messages.getString("UI.btnBtnhostcount.toolTipText")); //$NON-NLS-1$
		btnHostCount.setHorizontalAlignment(SwingConstants.RIGHT);
		btnHostCount.setContentAreaFilled(false);
		btnHostCount.setBorderPainted(false);
		btnHostCount.setBorder(null);
		btnHostCount.setForeground(new Color(0, 128, 0));
		btnHostCount.setBackground(Color.LIGHT_GRAY);
		jfrmUiGetHtml.getContentPane().add(btnHostCount, "2, 5, fill, fill");

		JPanel pnlOption = new JPanel();
		jfrmUiGetHtml.getContentPane().add(pnlOption, "4, 9, fill, fill");
		pnlOption
				.setLayout(new FormLayout(
						new ColumnSpec[] { ColumnSpec.decode("max(120dlu;default)"),
								FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("default:grow"), },
						new RowSpec[] { RowSpec.decode("default:grow"), }));

		JPanel panel_1 = new JPanel();
		pnlOption.add(panel_1, "1, 1, default, fill");
		panel_1.setBorder(new TitledBorder(null, Messages.getString("UI.panel_1.borderTitle"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.LEFT, TitledBorder.TOP, null, null));
		panel_1.setLayout(new FormLayout(new ColumnSpec[] { ColumnSpec.decode("143px"), },
				new RowSpec[] { RowSpec.decode("max(20px;default)"), FormSpecs.LINE_GAP_ROWSPEC,
						RowSpec.decode("max(20px;default)"), }));

		chckbxDownloadFrom = new JCheckBox(Messages.getString("UI.chckbxDownloadFrom.text"));
		panel_1.add(chckbxDownloadFrom, "1, 1, fill, fill");
		chckbxDownloadFrom.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent arg0) {
				if (arg0.isPopupTrigger()) {
					popupMenu.show(arg0.getComponent(), arg0.getX(), arg0.getY());
				}
			}
		});

		chckbxAddEbookInfo = new JCheckBox(Messages.getString("UI.chckbxAddEbookInfo.text"));
		chckbxAddEbookInfo.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (txtURL.getText().trim().equals("")) {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputFilePathFirst"));
					txtURL.requestFocus();
				} else if (chckbxAddEbookInfo.isSelected()) {
					cri = new CopyRightInfo(btnDownload);
					cri.setVisible(true);
				}
				chckbxAddEbookInfo.setSelected(false);
			}
		});
		panel_1.add(chckbxAddEbookInfo, "1, 3, fill, fill");

		JPanel panel_3 = new JPanel();
		panel_3.setBorder(new TitledBorder(null, Messages.getString("UI.panel_3.borderTitle"), TitledBorder.LEADING, //$NON-NLS-1$
				TitledBorder.TOP, null, null));
		pnlOption.add(panel_3, "3, 1, fill, fill");
		panel_3.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), }, new RowSpec[] {
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));

		chckbxOneFilePer = new JCheckBox(Messages.getString("UI.chckbxOneFilePer.text")); //$NON-NLS-1$
		chckbxOneFilePer.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent arg0) {
				// remember Checkbox one file per chapter state
				Config.put(EnumConfigKey.REMEMBER_ONE_PER_FILE, chckbxOneFilePer.isSelected(), true);
			}
		});
		panel_3.add(chckbxOneFilePer, "2, 1, fill, center");
		chckbxAddEbookInfo.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent arg0) {
				if (arg0.isPopupTrigger()) {
					popupMenu.show(arg0.getComponent(), arg0.getX(), arg0.getY());
				}
			}
		});

		JLabel lblTrngThi = new JLabel(Messages.getString("UI.lblTrngThi.text"));
		jfrmUiGetHtml.getContentPane().add(lblTrngThi, "2, 11, right, default");

		lblStatus = new JLabel(Messages.getString("UI.lblStatus.text"));
		jfrmUiGetHtml.getContentPane().add(lblStatus, "4, 11, 3, 1, fill, center");

		progressBar = new JProgressBar();
		jfrmUiGetHtml.getContentPane().add(progressBar, "2, 13, 5, 1, fill, fill");
		progressBar.setPreferredSize(new Dimension(100, 14));
		jfrmUiGetHtml.getContentPane().add(lblUrl, "2, 2, right, center");
		jfrmUiGetHtml.getContentPane().add(btnHelp, "4, 7, fill, top");
		jfrmUiGetHtml.getContentPane().add(cboPageConfigList, "4, 5, fill, fill");
		jfrmUiGetHtml.getContentPane().add(txtURL, "4, 2, fill, fill");
		jfrmUiGetHtml.getContentPane().add(btnResume, "6, 7, fill, center");
		jfrmUiGetHtml.getContentPane().add(btnCancel, "6, 5, fill, center");
		jfrmUiGetHtml.getContentPane().add(btnDownload, "6, 2, fill, center");

		JPanel panel = new JPanel();
		jfrmUiGetHtml.getContentPane().add(panel, "2, 15, 5, 1, fill, fill");
		panel.setBorder(new TitledBorder(null, Messages.getString("UI.panel.borderTitle"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.LEFT, TitledBorder.TOP, null, null));
		panel.setLayout(new GridLayout(0, 1, 0, 0));

		JScrollPane scrollPane = new JScrollPane();
		scrollPane.setAutoscrolls(true);
		scrollPane.setVerticalScrollBarPolicy(ScrollPaneConstants.VERTICAL_SCROLLBAR_ALWAYS);
		panel.add(scrollPane);

		txtLog = new JTextArea();
		txtLog.setDisabledTextColor(new Color(255, 255, 255));
		txtLog.setBackground(Color.GRAY);
		txtLog.setForeground(Color.GREEN);
		txtLog.setEditable(false);
		txtLog.setFont(new Font("SansSerif", Font.PLAIN, 11));
		scrollPane.setViewportView(txtLog);
	}
}
