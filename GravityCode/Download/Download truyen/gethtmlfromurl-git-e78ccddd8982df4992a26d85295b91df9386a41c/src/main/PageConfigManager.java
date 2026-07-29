package main;

import java.awt.Color;
import java.awt.ComponentOrientation;
import java.awt.Dimension;
import java.awt.EventQueue;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.MouseWheelEvent;
import java.awt.event.MouseWheelListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.ResourceBundle;

import javax.swing.DropMode;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;
import javax.swing.border.EmptyBorder;
import javax.swing.border.TitledBorder;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonValue;
import common.Enumeration;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.GetHtmlCsMix;
import mkgethtml.GetHtmlCss;
import mkgethtml.SettingOption;
import models.PageConfig;
import resource.text.Messages;
import utils.UrlHandler;
import utils.cloudflarebypass.CloudFlareByPass;

public class PageConfigManager extends JFrame {

	enum FONT_TYPE {
		NORMAL, ADD, EDIT, DELETE, NONE, DUPLICATE
	}

	/**
	*
	*/
	private static final long serialVersionUID = 1L;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				try {
					PageConfigManager frame = new PageConfigManager();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JPanel contentPane;
	private JTextField txtChapterContent;
	private JTextField txtChapterTitle;
	private JTextField txtListChapter;
	private JTextField txtPagePattern;
	private JTextField txtHost;
	JButton btnTestListChapter;
	JButton btnTestChapterTitle;
	JButton btnTestChapterContent;
	JButton btnSave;
	JButton btnCancel;
	JButton btnDelete;
	JButton btnEdit;
	JButton btnAdd;
	JButton btnRefresh;
	JComboBox<Enumeration.OverMaxSizePageCountState> cboPageStateWhenOver;
	JComboBox<PageConfig> cboPageConfigList;
	public JTextArea txtLog;
	JTextArea txtGuide;
	JCheckBox chckboxUseForManualGET;
	JCheckBox chckbxRevertListChapter;
	JCheckBox chckbxngPathIsAbsoluted;
	FONT_TYPE actionType = FONT_TYPE.NORMAL;
	private JScrollPane scrollPaneGuide;
	private JTextField txtCssRemoveContent;
	private JTextField txtCssTestAll;
	private JButton btnTestAll;
	private JPanel pnlButtons;
	private Element eDivListChapter;
	private JCheckBox chkTestSelectAll;
	private JPanel panelLogButtons;
	private JButton btnSmall;
	private JButton btnBig;
	private JButton btnDefault;
	private JPanel panelMasterQuery;

	private JTextField txtFilter;
	private JTabbedPane tabbedPane;
	private JScrollPane scrollPaneScript;
	private JTextArea txtScript;
	private JButton btnClearLog;
	private JButton btnDuplicate;
	private JTabbedPane tabbedPaneConfig;
	private JPanel pnlLeechCommon;
	private JPanel pnlPageOption;
	private JPanel panelChooseHost;
	private JCheckBox chkForumType;
	private JCheckBox chkIsVietNamHost;
	private JCheckBox chkIsUseJsoupGet;
	private JCheckBox chckbxEnableChapterSign;
	private JCheckBox chckbxBypassCloudflare;
	private JPanel panelChapterCssSelector;
	private JPanel panelChapterLinkConfig;
	private JButton btnTestFilter;
	private JPanel panelTestAddition;
	private JLabel lblCookies;
	private JTextField txtCookies;

	/**
	 * To get chapter content after chapter title, cache
	 */
	private Document documentTestCache = null;
	private JCheckBox chckbxUseBruteForce;

	/**
	 * Create the frame.
	 */
	public PageConfigManager() {
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));

		setIconImage(Toolkit.getDefaultToolkit().getImage(PageConfigManager.class.getResource("/resource/box-16.png")));
		setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			e2.printStackTrace();
		}

		addWindowListener(new WindowAdapter() {
			@Override
			public void windowOpened(WindowEvent arg0) {
				GetListToCombo("");
				setComponentEnable(false);

			}

		});
		setTitle(ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.this.title")); //$NON-NLS-1$ //$NON-NLS-2$
		setBounds(100, 100, 900, 600);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		setContentPane(contentPane);
		contentPane.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, FormSpecs.GROWING_BUTTON_COLSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, FormSpecs.DEFAULT_COLSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("max(29dlu;default)"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("max(400px;min)"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("default:grow"), }));

		panelChooseHost = new JPanel();
		contentPane.add(panelChooseHost, "2, 2, fill, fill");
		panelChooseHost.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("right:90px"),
						FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), FormSpecs.RELATED_GAP_COLSPEC,
						ColumnSpec.decode("160px"), FormSpecs.RELATED_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("fill:default"), }));

		JLabel lblChoosePage = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblChoosePage.text"));
		panelChooseHost.add(lblChoosePage, "2, 2, right, fill");
		lblChoosePage.setToolTipText(ResourceBundle.getBundle("resource.text.messages")
				.getString("PageConfigManager.lblChoosePage.toolTipText"));

		cboPageConfigList = new JComboBox<>();
		panelChooseHost.add(cboPageConfigList, "4, 2, fill, fill");
		cboPageConfigList.setFont(new Font("Tahoma", Font.PLAIN, 16));

		txtFilter = new JTextField();
		panelChooseHost.add(txtFilter, "6, 2, fill, fill");
		txtFilter.setBackground(SystemColor.control);
		txtFilter.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				GetListToCombo(txtFilter.getText());
			}
		});

		txtFilter.setBorder(new TitledBorder(UIManager.getBorder("ComboBox.border"),
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.txtFilter.borderTitle"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.LEFT, TitledBorder.TOP, null, new Color(0, 0, 0)));
		txtFilter.setText("");
		txtFilter.setColumns(10);

		tabbedPaneConfig = new JTabbedPane(JTabbedPane.TOP);
		contentPane.add(tabbedPaneConfig, "2, 4, fill, fill");

		pnlLeechCommon = new JPanel();
		tabbedPaneConfig.addTab(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.panel_6.title"), null, //$NON-NLS-1$ //$NON-NLS-2$
				pnlLeechCommon, null);
		pnlLeechCommon.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("max(237dlu;default):grow"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.MIN_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("fill:default:grow"), FormSpecs.LINE_GAP_ROWSPEC, }));

		JPanel panelPageInfo = new JPanel();
		pnlLeechCommon.add(panelPageInfo, "2, 2");
		panelPageInfo.setBorder(new TitledBorder(null,
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_2.borderTitle"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.LEADING, TitledBorder.TOP, null, null));
		panelPageInfo.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("112px"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("196px:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.MIN_ROWSPEC, FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.MIN_ROWSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.MIN_ROWSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.MIN_ROWSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		JButton button = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnHelp.text")); //$NON-NLS-1$ //$NON-NLS-2$
		button.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (JOptionPane.showConfirmDialog(null,
						"PagePattern: là dạng truy vấn phân trang của trang web.\n"
								+ " Ví dụ: \"http://abc.xy/page-10\" thì \"page-\" là PagePattern, số 10 là 1 con số chương trình sẽ tự tăng nó.\n"
								+ " Hoặc dạng \"http://abc.xy/page/3\" thì \"page/\" là PagePattern.\n\n"
								+ "CssSeletor: là truy vấn cssQuery để tìm ra thẻ mong muốn.\n"
								+ " - Div List Chapter: là cssQuery lấy ra được thẻ chứa danh sách link các chapter(tức thẻ a).\n"
								+ "	  Nhấn nút TEST để kiểm tra cssQuery nếu đúng sẽ dạng Số trang: [Tổng số trang].\n"
								+ " - Div chapter Title: là cssQuery lấy ra thẻ chứa TITLE của chapter(ví dụ thẻ a, h2).\n"
								+ " - Div Chapter Content: là cssQuery lấy ra thẻ chứa TEXT truyện của link.\n\n"
								+ "Tham khảo thêm về CssSeletor trên W3Schools.com và thử bằng chính trình duyệt.\n\n"
								+ "XEM VIDEO HƯỚNG DẪN TRÊN YOUTUBE",
						Messages.getGlobalString("title.help"), JOptionPane.YES_NO_OPTION) == JOptionPane.YES_OPTION) {
					try {
						java.awt.Desktop.getDesktop().browse(new URI("https://youtu.be/IKl3uKBxJ6I"));
					} catch (IOException | URISyntaxException e) {
						e.printStackTrace();
					}
				}
			}
		});
		panelPageInfo.add(button, "2, 1, right, top");

		chckboxUseForManualGET = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxIsManualGet.text")); //$NON-NLS-1$
		chckboxUseForManualGET.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent arg0) {
				if (chckboxUseForManualGET.isSelected()) {
					txtPagePattern.setEnabled(false);
					cboPageStateWhenOver.setEnabled(false);
				} else {
					txtPagePattern.setEnabled(true);
					cboPageStateWhenOver.setEnabled(true);
				}
			}
		});

		chckboxUseForManualGET.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxIsManualGet.toolTipText"));
		panelPageInfo.add(chckboxUseForManualGET, "4, 1, 2, 1, left, center");

		JLabel lblMTrang = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblHost.text")); //$NON-NLS-1$ //$NON-NLS-2$
		panelPageInfo.add(lblMTrang, "2, 3, right, center");

		txtHost = new JTextField();
		txtHost.setColumns(10);
		panelPageInfo.add(txtHost, "4, 3, fill, top");

		JLabel lblPagePattern = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblPagePattern.text")); //$NON-NLS-1$ //$NON-NLS-2$
		lblPagePattern.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblPagePattern.toolTipText")); //$NON-NLS-1$
		panelPageInfo.add(lblPagePattern, "2, 5, right, center");

		txtPagePattern = new JTextField();
		txtPagePattern.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.txtPagePattern.toolTipText")); //$NON-NLS-1$
		txtPagePattern.setColumns(10);
		panelPageInfo.add(txtPagePattern, "4, 5, fill, top");

		cboPageStateWhenOver = new JComboBox<>();// $NON-NLS-1$
		cboPageStateWhenOver.addItem(Enumeration.OverMaxSizePageCountState.MOVE_TO_FIRST);
		cboPageStateWhenOver.addItem(Enumeration.OverMaxSizePageCountState.MOVE_TO_LAST);
		cboPageStateWhenOver.addItem(Enumeration.OverMaxSizePageCountState.MOVE_TO_PAGE_WITHOUT_CHAPTER_LIST);

		JLabel lblOverPageState = new JLabel(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblOverPageState.text")); //$NON-NLS-1$
		lblOverPageState.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.label.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		panelPageInfo.add(lblOverPageState, "2, 7, right, center");
		// //$NON-NLS-2$
		cboPageStateWhenOver.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxOverloadGotoFirst.toolTipText")); //$NON-NLS-1$
		panelPageInfo.add(cboPageStateWhenOver, "4, 7, fill, top");

		JPanel panelGuide = new JPanel();
		pnlLeechCommon.add(panelGuide, "2, 4");
		panelGuide.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("right:max(80dlu;default)"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("193px:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.LINE_GAP_ROWSPEC, RowSpec.decode("fill:default:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		JLabel lblGuide = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblGuide.text"));
		panelGuide.add(lblGuide, "2, 2");
		lblGuide.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblGuide.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$

		tabbedPane = new JTabbedPane(JTabbedPane.BOTTOM);
		panelGuide.add(tabbedPane, "4, 2");

		scrollPaneGuide = new JScrollPane();
		tabbedPane.addTab(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.scrollPane_1.title"), //$NON-NLS-1$ //$NON-NLS-2$
				null, scrollPaneGuide,
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.scrollPane_1.tooltip")); //$NON-NLS-1$ //$NON-NLS-2$
		txtGuide = new JTextArea();
		txtGuide.setFont(UIManager.getFont("TextArea.font"));
		txtGuide.setForeground(new Color(240, 248, 255));
		txtGuide.setBackground(new Color(0, 128, 0));
		txtGuide.setText("");
		scrollPaneGuide.setViewportView(txtGuide);

		scrollPaneScript = new JScrollPane();
		tabbedPane.addTab(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.scrollPane_2.title"), //$NON-NLS-1$ //$NON-NLS-2$
				null, scrollPaneScript,
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.scrollPane_2.tooltip")); //$NON-NLS-1$ //$NON-NLS-2$
		tabbedPane.setEnabledAt(1, true);

		txtScript = new JTextArea();
		txtScript.setCaretColor(Color.WHITE);
		txtScript.setText("");
		txtScript.setForeground(new Color(240, 248, 255));
		txtScript.setFont(UIManager.getFont("TextArea.font"));
		txtScript.setBackground(Color.GRAY);
		scrollPaneScript.setViewportView(txtScript);

		JPanel panelListChapter = new JPanel();
		tabbedPaneConfig.addTab(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.panel_3.title"), null, //$NON-NLS-1$ //$NON-NLS-2$
				panelListChapter, null);
		panelListChapter.setBorder(new TitledBorder(null,
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_3.borderTitle"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.LEADING, TitledBorder.TOP, null, null));
		panelListChapter.setLayout(new FormLayout(
				new ColumnSpec[] { ColumnSpec.decode("280px:grow"), FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.MIN_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("max(53dlu;min)"), FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
						FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("default:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		panelMasterQuery = new JPanel();
		panelMasterQuery.setBorder(new TitledBorder(
				new TitledBorder(UIManager.getBorder("TitledBorder.border"), "", TitledBorder.LEADING, TitledBorder.TOP,
						null, new Color(0, 0, 0)),
				"Browse Console Query", TitledBorder.LEADING, TitledBorder.TOP, null, new Color(0, 0, 0)));
		panelListChapter.add(panelMasterQuery, "1, 2, fill, fill");
		panelMasterQuery
				.setLayout(new FormLayout(
						new ColumnSpec[] { ColumnSpec.decode("75dlu"), FormSpecs.LABEL_COMPONENT_GAP_COLSPEC,
								ColumnSpec.decode("108px:grow"), FormSpecs.LABEL_COMPONENT_GAP_COLSPEC,
								FormSpecs.MIN_COLSPEC, FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
						new RowSpec[] { RowSpec.decode("23px"), }));

		chkTestSelectAll = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxTestSelectAll.text"));
		panelMasterQuery.add(chkTestSelectAll, "1, 1");

		txtCssTestAll = new JTextField();
		panelMasterQuery.add(txtCssTestAll, "3, 1");
		txtCssTestAll.setText("");
		txtCssTestAll.setColumns(10);

		btnTestAll = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnTestAll.text"));
		panelMasterQuery.add(btnTestAll, "5, 1");
		btnTestAll.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				getTestAllHtml();

			}
		});
		chkTestSelectAll.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent arg0) {
				if (chkTestSelectAll.isSelected()) {
					chkTestSelectAll.setText(Messages.getString("PageConfigManager.chkTestSelectAll.text"));
				} else {
					chkTestSelectAll.setText(Messages.getString("PageConfigManager.chkTestSelectAll.textSelectOne"));
				}
			}
		});

		panelTestAddition = new JPanel();
		panelTestAddition.setBorder(
				new TitledBorder(UIManager.getBorder("TitledBorder.border"), "Cookies & More..(Use for test only)",
						TitledBorder.LEADING, TitledBorder.TOP, null, new Color(0, 0, 0)));
		panelListChapter.add(panelTestAddition, "1, 4, fill, fill");
		panelTestAddition.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, FormSpecs.DEFAULT_COLSPEC,
						FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("default:grow"), }));

		lblCookies = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblCookies.text")); //$NON-NLS-1$ //$NON-NLS-2$
		panelTestAddition.add(lblCookies, "2, 2, right, default");

		txtCookies = new JTextField();
		txtCookies.setText("");
		panelTestAddition.add(txtCookies, "4, 2, fill, fill");
		txtCookies.setColumns(10);

		panelChapterLinkConfig = new JPanel();
		panelListChapter.add(panelChapterLinkConfig, "1, 6, fill, fill");
		panelChapterLinkConfig.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("75dlu"),
						FormSpecs.RELATED_GAP_COLSPEC, FormSpecs.DEFAULT_COLSPEC, FormSpecs.RELATED_GAP_COLSPEC,
						FormSpecs.DEFAULT_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));

		chckbxngPathIsAbsoluted = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxChapterLinkIsAsoluted.text"));
		panelChapterLinkConfig.add(chckbxngPathIsAbsoluted, "4, 2");
		chckbxngPathIsAbsoluted.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxChapterLinkIsAbsoluted.toolTipText")); //$NON-NLS-1$
		chckbxngPathIsAbsoluted.setSelected(true);

		chckbxRevertListChapter = new JCheckBox(ResourceBundle.getBundle("resource.text.messages")
				.getString("PageConfigManager.chckbxRevertListChapter.text"));
		panelChapterLinkConfig.add(chckbxRevertListChapter, "6, 2");
		chckbxRevertListChapter.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxRevertListChapter.toolTipText"));

		panelChapterCssSelector = new JPanel();
		panelListChapter.add(panelChapterCssSelector, "1, 8, fill, fill");
		panelChapterCssSelector.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("75dlu"),
						FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("max(28dlu;default):grow"),
						FormSpecs.RELATED_GAP_COLSPEC, FormSpecs.MIN_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
						FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));

		JLabel lblDivchapter = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.lblDivchapter.text")); //$NON-NLS-1$ //$NON-NLS-2$
		panelChapterCssSelector.add(lblDivchapter, "2, 2, right, fill");
		lblDivchapter.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblDivchapter.toolTipText")); //$NON-NLS-1$
		lblDivchapter.setHorizontalAlignment(SwingConstants.CENTER);

		txtListChapter = new JTextField();
		panelChapterCssSelector.add(txtListChapter, "4, 2");
		txtListChapter.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.txtListChapter.toolTipText")); //$NON-NLS-1$
		txtListChapter.setComponentOrientation(ComponentOrientation.LEFT_TO_RIGHT);
		txtListChapter.setDropMode(DropMode.INSERT);
		txtListChapter.setHorizontalAlignment(SwingConstants.LEFT);

		btnTestListChapter = new JButton(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.btnTestListChapter.text")); //$NON-NLS-1$
		panelChapterCssSelector.add(btnTestListChapter, "6, 2");

		JLabel lblDivchapterTitle = new JLabel(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblDivchapterTitle.text")); //$NON-NLS-1$
		panelChapterCssSelector.add(lblDivchapterTitle, "2, 4, right, fill");
		lblDivchapterTitle.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblDivchapterTitle.toolTipText"));

		txtChapterTitle = new JTextField();
		panelChapterCssSelector.add(txtChapterTitle, "4, 4");
		txtChapterTitle.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.txtChapterTitle.toolTipText")); //$NON-NLS-1$
		txtChapterTitle.setColumns(10);

		btnTestChapterTitle = new JButton(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.btnTestChapterTitle.text")); //$NON-NLS-1$
		panelChapterCssSelector.add(btnTestChapterTitle, "6, 4");

		JLabel lblDivchapterContent = new JLabel(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblDivchapterContent.text")); //$NON-NLS-1$
		panelChapterCssSelector.add(lblDivchapterContent, "2, 6, right, fill");
		lblDivchapterContent.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.lblDivchapterContent.toolTipText"));

		txtChapterContent = new JTextField();
		panelChapterCssSelector.add(txtChapterContent, "4, 6");
		txtChapterContent.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.txtChapterContent.toolTipText")); //$NON-NLS-1$
		txtChapterContent.setColumns(10);

		btnTestChapterContent = new JButton(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.btnTestChapterContent.text")); //$NON-NLS-1$
		panelChapterCssSelector.add(btnTestChapterContent, "6, 6");

		JLabel labelCssRemoveContent = new JLabel(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.labelCssRemoveContent.text")); //$NON-NLS-1$
		panelChapterCssSelector.add(labelCssRemoveContent, "2, 8, right, fill");
		labelCssRemoveContent.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.labelCssRemoveContent.toolTipText"));

		txtCssRemoveContent = new JTextField();
		panelChapterCssSelector.add(txtCssRemoveContent, "4, 8");
		txtCssRemoveContent.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.txtCssRemoveContent.toolTipText")); //$NON-NLS-1$
		txtCssRemoveContent.setColumns(10);

		btnTestFilter = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnTest.text")); //$NON-NLS-1$ //$NON-NLS-2$
		btnTestFilter.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				filterDocument();
			}
		});
		panelChapterCssSelector.add(btnTestFilter, "6, 8");
		btnTestChapterContent.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				getTestChapterContent();
			}
		});
		btnTestChapterTitle.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				getTestChapterTitle();
			}
		});
		btnTestListChapter.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				getTestDivListChapter();
			}
		});

		pnlPageOption = new JPanel();
		tabbedPaneConfig.addTab(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.panel_7.title"), null, //$NON-NLS-1$ //$NON-NLS-2$
				pnlPageOption, null);
		pnlPageOption.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, FormSpecs.GROWING_BUTTON_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
						FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));

		chkForumType = new JCheckBox(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.chkForumType.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlPageOption.add(chkForumType, "2, 2");

		chkIsVietNamHost = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chkIsVietNamHost.text")); //$NON-NLS-1$
		pnlPageOption.add(chkIsVietNamHost, "2, 4");

		chkIsUseJsoupGet = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chkIsUseJsoupGet.text")); //$NON-NLS-1$
		chkIsUseJsoupGet.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chkIsUseJsoupGet.toolTipText")); //$NON-NLS-1$
		pnlPageOption.add(chkIsUseJsoupGet, "2, 6");

		chckbxEnableChapterSign = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxEnableChapterSign.text")); //$NON-NLS-1$
		pnlPageOption.add(chckbxEnableChapterSign, "2, 8");

		chckbxBypassCloudflare = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxBypassCloudflare.text")); //$NON-NLS-1$
		pnlPageOption.add(chckbxBypassCloudflare, "2, 10");

		chckbxUseBruteForce = new JCheckBox(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxUseBruteForce.text")); //$NON-NLS-1$
		chckbxUseBruteForce.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.chckbxUseBruteForce.toolTipText")); //$NON-NLS-1$
		pnlPageOption.add(chckbxUseBruteForce, "2, 12");

		pnlButtons = new JPanel();
		contentPane.add(pnlButtons, "4, 2, 1, 3, right, top");
		pnlButtons.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("max(65dlu;pref):grow"),
						FormSpecs.RELATED_GAP_COLSPEC, },
				new RowSpec[] { RowSpec.decode("5dlu"), RowSpec.decode("fill:30px"), FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("15dlu"), FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px:grow"), }));

		btnRefresh = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnRefresh.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlButtons.add(btnRefresh, "2, 2, fill, center");
		btnRefresh.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.btnRefresh.toolTipText")); //$NON-NLS-1$

		btnAdd = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnAdd.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlButtons.add(btnAdd, "2, 6, fill, fill");
		// duplicate
		btnDuplicate = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnDuplicate.text")); //$NON-NLS-1$ //$NON-NLS-2$

		pnlButtons.add(btnDuplicate, "2, 8, fill, fill");

		btnEdit = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnEdit.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlButtons.add(btnEdit, "2, 10, fill, center");

		btnDelete = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnDelete.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlButtons.add(btnDelete, "2, 12, fill, center");
		btnDelete.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				setLogColorAndActionType(FONT_TYPE.DELETE);
				setComponentEnable(true);

			}
		});

		btnSave = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnSave.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlButtons.add(btnSave, "2, 14, fill, center");

		btnCancel = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnCancel.text")); //$NON-NLS-1$ //$NON-NLS-2$
		pnlButtons.add(btnCancel, "2, 16, fill, top");
		btnCancel.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				setLogColorAndActionType(FONT_TYPE.NONE);
				setComponentEnable(false);
				// clear filter
				if (txtFilter.getText().length() > 0) {
					txtFilter.setText("");
					GetListToCombo("");
				}
			}
		});
		btnSave.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				saveAction();
			}

		});
		btnEdit.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				setLogColorAndActionType(FONT_TYPE.EDIT);
				setComponentEnable(true);

			}
		});
		btnAdd.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				setLogColorAndActionType(FONT_TYPE.ADD);
				setComponentEnable(true);

			}
		});
		btnRefresh.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				GetListToCombo("");
			}
		});
		btnDuplicate.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				setLogColorAndActionType(FONT_TYPE.DUPLICATE);
				setComponentEnable(true);

			}
		});
		JScrollPane logScrollPane = new JScrollPane();
		logScrollPane.addMouseWheelListener(new MouseWheelListener() {
			@Override
			public void mouseWheelMoved(MouseWheelEvent e) {
				if (e.isControlDown() && e.getWheelRotation() > 0) {
					btnSmall.doClick();
				} else if (e.isControlDown() && e.getWheelRotation() < 0) {
					btnBig.doClick();
				} else {
					logScrollPane.requestFocus();
				}
			}
		});
		contentPane.add(logScrollPane, "2, 6, 3, 1, fill, fill");
		logScrollPane.setBorder(new TitledBorder(null, "Logs", TitledBorder.LEFT, TitledBorder.TOP, null, null));

		txtLog = new JTextArea();

		txtLog.setWrapStyleWord(true);
		txtLog.setFont(new Font("Monospaced", Font.PLAIN, 12));
		logScrollPane.setViewportView(txtLog);
		txtLog.setForeground(new Color(0, 191, 255));
		txtLog.setBackground(new Color(105, 105, 105));
		txtLog.setEditable(false);

		panelLogButtons = new JPanel();
		logScrollPane.setColumnHeaderView(panelLogButtons);
		panelLogButtons.setLayout(new FlowLayout(FlowLayout.LEFT, 5, 5));

		btnDefault = new JButton("");
		btnDefault.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.btnDefault.toolTipText")); //$NON-NLS-1$
		btnDefault.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				txtLog.setFont(new Font("Monospaced", Font.PLAIN, 12));
			}
		});
		btnDefault.setPreferredSize(new Dimension(16, 16));
		btnDefault.setIconTextGap(0);
		btnDefault.setIcon(new ImageIcon(PageConfigManager.class.getResource("/resource/Zoom To Actual Size-16.png")));
		btnDefault.setBorderPainted(false);
		btnDefault.setContentAreaFilled(false);
		panelLogButtons.add(btnDefault);

		btnBig = new JButton("");
		btnBig.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnBig.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		btnBig.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				int size = txtLog.getFont().getSize();
				if (size < 24) {
					txtLog.setFont(new Font("Monospaced", Font.PLAIN, ++size));
				} else {
					txtLog.setFont(new Font("Monospaced", Font.PLAIN, 24));
				}
			}
		});
		btnBig.setPreferredSize(new Dimension(16, 16));
		btnBig.setIconTextGap(0);
		btnBig.setIcon(new ImageIcon(PageConfigManager.class.getResource("/resource/Zoom In-16.png")));
		btnBig.setBorderPainted(false);
		btnBig.setContentAreaFilled(false);
		panelLogButtons.add(btnBig);

		btnSmall = new JButton("");
		btnSmall.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("PageConfigManager.btnSmall.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		btnSmall.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				int size = txtLog.getFont().getSize();
				if (size > 6) {
					txtLog.setFont(new Font("Monospaced", Font.PLAIN, --size));
				} else {
					txtLog.setFont(new Font("Monospaced", Font.PLAIN, 3));
				}
			}
		});
		btnSmall.setPreferredSize(new Dimension(16, 16));
		btnSmall.setIconTextGap(0);
		btnSmall.setIcon(new ImageIcon(PageConfigManager.class.getResource("/resource/Zoom Out-16.png")));
		btnSmall.setBorderPainted(false);
		btnSmall.setContentAreaFilled(false);
		panelLogButtons.add(btnSmall);

		btnClearLog = new JButton("");
		btnClearLog.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent e) {
				txtLog.setText("");
			}
		});
		btnClearLog.setToolTipText(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("PageConfigManager.btnClearLog.toolTipText")); //$NON-NLS-1$
		btnClearLog.setIcon(new ImageIcon(PageConfigManager.class.getResource("/resource/Delete-16-hover.png")));
		btnClearLog.setPreferredSize(new Dimension(16, 16));
		btnClearLog.setIconTextGap(0);
		btnClearLog.setContentAreaFilled(false);
		btnClearLog.setBorderPainted(false);
		panelLogButtons.add(btnClearLog);
	}

	void GetListToCombo(String filterChain) {

		cboPageConfigList.removeAllItems();
		if (filterChain.length() < 3) {
			for (PageConfig pageConfig : Config.getAllHostConfig()) {
				cboPageConfigList.addItem(pageConfig);
			}
		} else {
			for (PageConfig pageConfig : Config.getAllHostConfig()) {
				if (pageConfig.getPageCode().contains(filterChain)) {
					cboPageConfigList.addItem(pageConfig);
				}
			}
		}
		actionType = FONT_TYPE.NONE;
	}

	/**
	 * Return cookies string
	 * 
	 * @return
	 */
	Map<String, String> getCookies() {

		Map<String, String> cookies = new HashMap<String, String>();
		String cookie = txtCookies.getText().trim();
		if (!cookie.isEmpty()) {
			cookies = UrlHandler.getCookiesMap(cookie);
		}
		return cookies;
	}

	/**
	 * Send request using JSOUP
	 * 
	 * @param url
	 * @return
	 * @throws IOException
	 */
	Document getDocumentByUrl(String url) throws IOException {
		Map<String, String> cookies = getCookies();
		Document document = null;
		if (chckbxBypassCloudflare.isSelected() && cookies.size() == 0) {
			// not input cookies that already has cloudflare cookies, try to get
			// it
			document = CloudFlareByPass.byPassCloudFlareGetDocument(url, 1);
		} else {
			document = Jsoup.connect(url).userAgent(Constant.USER_AGENT).timeout(CommonValue.getTimeout())
					.cookies(cookies).ignoreHttpErrors(true).get();
		}
		return document;

	}

	void getTestAllHtml() {
		txtLog.setText("");
		if (txtHost.getText() != "" && txtPagePattern.getText() != "") {
			try {
				URL u = new URL(txtHost.getText().trim());

				if (!txtCssTestAll.getText().equals("")) {

					Document doc = getDocumentByUrl(u.toString());

					Elements testAll = doc.select(txtCssTestAll.getText().trim());

					if (testAll != null) {
						txtLog.setText("CHILD COUNT: " + (chkTestSelectAll.isSelected() == true ? testAll.size()
								: testAll.first().childNodeSize()));
						txtLog.append("\nHTML:\n\n" + (chkTestSelectAll.isSelected() == true ? testAll.toString()
								: testAll.first().toString()));

					}

				} else {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.clickTestAllBefore"));
					return;
				}

			} catch (IOException e) {

				StringBuilder sb = new StringBuilder();
				sb.append(e.getMessage() + "\n");
				for (int i = 0; i < e.getStackTrace().length; i++) {
					sb.append(e.getStackTrace()[i] + "\n");
				}

				txtLog.append("Error:\n" + sb.toString()
						+ "\n\nLưu ý nếu lỗi 3xx(là do trang bị chuyển hướng)\nhoặc 4xx là do không đủ quyền\n"
						+ "Lỗi không đủ quyền là do trang đó chặn tools :)))");
				e.printStackTrace();
			}
		} else {
			JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputPattenAndHostFirst"));
		}
	}

	void getTestChapterTitle() {
		if (txtHost.getText() != "" && txtPagePattern.getText() != "") {
			try {
				if (txtListChapter.getText().trim() == "") {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputDivListChapterFirst"));
					return;
				}
				// get listchapter if not press
				if (eDivListChapter == null) {
					btnTestListChapter.doClick();
				}
				txtLog.setText("");

				if (eDivListChapter != null) {
					String chapterUrl = eDivListChapter.select("a").eq(0).attr("href").toString();
					int i = 1;
					while (chapterUrl.contains("javascript:") && !chapterUrl.startsWith("http://")) {
						chapterUrl = eDivListChapter.select("a").eq(i).attr("href").toString();
						i++;
					}

					documentTestCache = getDocumentByUrl(chapterUrl);

					txtLog.setText("Title: " + documentTestCache.select(txtChapterTitle.getText().trim()).text());
					txtLog.append("\n\n\n--------------------------------\nContent:\n"
							+ documentTestCache.select(txtChapterTitle.getText().trim()).toString());
				} else {
					txtLog.append(Messages.getGlobalString("log.notFoundChapterPlsClickTestAll") + "\n");
				}

			} catch (IOException e) {

				StringBuilder sb = new StringBuilder();
				sb.append(e.getMessage() + "\n");
				for (int i = 0; i < e.getStackTrace().length; i++) {
					sb.append(e.getStackTrace()[i] + "\n");
				}

				txtLog.append("Error:\n" + sb.toString()
						+ "\n\nLưu ý nếu lỗi 3xx(là do trang bị chuyển hướng)\nhoặc 4xx là do không đủ quyền\n"
						+ "Lỗi không đủ quyền là do trang đó chặn tools :)))");
				e.printStackTrace();
			}
		} else {
			JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputPattenAndHostFirst"));
		}
	}

	void getTestDivListChapter() {
		txtLog.setText("");

		if (txtHost.getText() != "" && txtPagePattern.getText() != "") {
			try {
				Document doc = getDocumentByUrl(txtHost.getText());

				eDivListChapter = null;
				if (chkForumType.isSelected()) {
					eDivListChapter = GetHtmlCsMix.getTotalPageOfForum(doc, txtHost.getText(), txtListChapter.getText(),
							txtPagePattern.getText(), new JLabel(), txtLog);

				} else if (txtListChapter.getText().trim().contains("{")) {

					String cssQueryGetListChapter = txtListChapter.getText().replaceAll("\\$([\\w\\d\\\\W\\D=\\&\\;])*",
							"");

					cssQueryGetListChapter = cssQueryGetListChapter.substring(0, cssQueryGetListChapter.indexOf("{"));

					ArrayList<String> arr = GetHtmlCss.getSpecialStringFromQuery(txtListChapter.getText());

					eDivListChapter = GetHtmlCss.getListTagAUrlSpecialCssQuery(doc, cssQueryGetListChapter, arr);
				} else if (txtListChapter.getText().trim().contains(";")) {
					eDivListChapter = doc.select(txtListChapter.getText().trim().split(";")[0]).first();
				} else {
					eDivListChapter = doc.select(txtListChapter.getText().trim()).first();
				}

				URL u = new URL(txtHost.getText().trim());

				Thread t = new Thread(new Runnable() {
					@Override
					public void run() {
						txtLog.setText(String.format(Messages.getGlobalString("txtLog.totalChapter"),
								eDivListChapter.children().size()));

						txtLog.append(String.format(Messages.getGlobalString("txtLog.listChapterLink")));
						// spect host
						String patterHost = UrlHandler.getHostFromPattern(txtListChapter.getText(), txtHost.getText());
						String newLink = "";
						for (int i = 0; i < eDivListChapter.children().size(); i++) {
							if (!eDivListChapter.select("a").eq(i).attr("href").contains("javascript:")) {
								if (chckbxngPathIsAbsoluted.isSelected()) {
									newLink = UrlHandler
											.normalizeHost(eDivListChapter.select("a").eq(i).attr("href").toString());
									txtLog.append(newLink + "\n");
									eDivListChapter.select("a").eq(i).attr("href", newLink);
								} else {

									if (txtListChapter.getText().contains(";")) {
										if (i == 0) {
											patterHost = UrlHandler.getHostFromPattern(txtListChapter.getText(),
													txtHost.getText());
										}

										newLink = UrlHandler.normalizeHostAndPath(patterHost,
												eDivListChapter.select("a").eq(i).attr("href"), u.toString());
									} else {
										newLink = UrlHandler.normalizeHostAndPath(u.getHost(),
												eDivListChapter.select("a").eq(i).attr("href"), u.toString());
									}
									eDivListChapter.select("a").eq(i).attr("href", newLink);
									txtLog.append(newLink + "\n");
								}
							}

							txtLog.getScrollableTracksViewportHeight();
						}

					}
				});

				t.start();

			} catch (IOException e) {

				StringBuilder sb = new StringBuilder();
				sb.append(e.getMessage() + "\n");
				for (int i = 0; i < e.getStackTrace().length; i++) {
					sb.append(e.getStackTrace()[i] + "\n");
				}

				txtLog.append("Error:\n" + sb.toString()
						+ "\n\nLưu ý nếu lỗi 3xx(là do trang bị chuyển hướng)\nhoặc 4xx là do không đủ quyền\n"
						+ "Lỗi không đủ quyền là do trang đó chặn tools :)))");
				e.printStackTrace();
			}
		} else {
			JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputPattenAndHostFirst"));
		}

	}

	void getTestChapterContent() {
		txtLog.setText("");
		if (txtHost.getText() != "" && txtPagePattern.getText() != "") {
			try {
				if (txtListChapter.getText().trim() == "") {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputDivListChapterFirst"));
					return;
				}
				// get listchapter if not press
				if (eDivListChapter == null) {
					btnTestListChapter.doClick();
				}
				txtLog.setText("");

				if (eDivListChapter != null) {
					String chapterUrl = eDivListChapter.select("a").eq(0).attr("href").toString();
					int i = 1;
					while (chapterUrl.contains("javascript:") && !chapterUrl.startsWith("http://")) {
						chapterUrl = eDivListChapter.select("a").eq(i).attr("href").toString();
						i++;
					}
					if (documentTestCache == null) {
						documentTestCache = getDocumentByUrl(chapterUrl);
					}

					txtLog.setText("Text: " + documentTestCache.select(txtChapterContent.getText().trim()).text());
					txtLog.append("\n\n\n--------------------------------\nContent: "
							+ documentTestCache.select(txtChapterContent.getText().trim()).toString());
				} else {
					txtLog.append(Messages.getGlobalString("log.notFoundChapterPlsClickTestAll") + "\n");
				}

			} catch (IOException e) {

				StringBuilder sb = new StringBuilder();
				sb.append(e.getMessage() + "\n");
				for (int i = 0; i < e.getStackTrace().length; i++) {
					sb.append(e.getStackTrace()[i] + "\n");
				}

				txtLog.append("Error:\n" + sb.toString()
						+ "\n\nLưu ý nếu lỗi 3xx(là do trang bị chuyển hướng)\nhoặc 4xx là do không đủ quyền\n"
						+ "Lỗi không đủ quyền là do trang đó chặn tools :)))");
				e.printStackTrace();
			}
		} else {
			JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.inputPattenAndHostFirst"));
		}
	}

	protected void filterDocument() {
		Document doc = documentTestCache.clone();
		Elements element = GetHtmlCss.filterHtml(doc.select("body"), txtCssRemoveContent.getText());
		txtLog.setText("AFTER FILTER:\n\n\nText: " + element.select(txtChapterContent.getText().trim()).text());
		txtLog.append("\n\n\n--------------------------------\nContent: "
				+ element.select(txtChapterContent.getText().trim()).toString());
	}

	/**
	 * btnSave Event handler
	 */
	protected void saveAction() {
		PageConfig p;
		URL u = null;
		try {
			u = new URL(txtHost.getText().trim().toLowerCase());

			switch (actionType) {
			case ADD:
			case DUPLICATE:
				p = new PageConfig();
				if (!chckboxUseForManualGET.isSelected()) {
					p.setPageCode(u.getHost().toString().toLowerCase());
					p.setUrlPageTest(u.toString().toLowerCase());
					p.setPagingPattern(txtPagePattern.getText().trim().toLowerCase());
				} else {
					try {
						p.setPageCode(u.getHost().toString().toLowerCase());
						p.setUrlPageTest(u.toString().toLowerCase());
						p.setPagingPattern("");
					} catch (Exception e1) {

						e1.printStackTrace();
					}
				}

				p.setCssQueryGetListChapter(txtListChapter.getText());
				p.setCssQueryGetChapterTitle(txtChapterTitle.getText().trim());
				p.setCssQueryGetChapterContent(txtChapterContent.getText().trim());
				p.setOverMaxSizePageCountState(
						(Enumeration.OverMaxSizePageCountState) cboPageStateWhenOver.getSelectedItem());
				p.setIsChapterLinkAsolute(chckbxngPathIsAbsoluted.isSelected());
				p.setIsManualGet(chckboxUseForManualGET.isSelected());
				p.setIsEnableChapterSign(chckbxEnableChapterSign.isSelected());
				p.setIsRevertChapterList(chckbxRevertListChapter.isSelected());
				p.setCssFilter(txtCssRemoveContent.getText());
				p.setTextGuide(txtGuide.getText());
				p.setScriptJS(txtScript.getText());
				p.setIsForumType(chkForumType.isSelected());
				p.setIsVietNameseHost(chkIsVietNamHost.isSelected());
				p.setIsUseJsoupGet(chkIsUseJsoupGet.isSelected());
				p.setByPassCloudFlare(chckbxBypassCloudflare.isSelected());

				if (Config.isSupportHost(p.getPageCode()) != 0) {
					JOptionPane.showMessageDialog(null, String.format(
							Messages.getGlobalString("notify.hostAlreadyExistTryEditFunction"), p.getPageCode()));
					return;
				} else {
					Config.addHost(p);
					txtLog.append(String.format(Messages.getGlobalString("log.addedHost"), p.getPageCode()));
				}

				break;
			case EDIT:
				p = new PageConfig();
				if (!chckboxUseForManualGET.isSelected()) {
					p.setPageCode(u.getHost().toString().toLowerCase());
					p.setUrlPageTest(u.toString().toLowerCase());
					p.setPagingPattern(txtPagePattern.getText().trim().toLowerCase());
				} else {
					try {
						p.setPageCode(u.getHost().toString().toLowerCase());
						p.setUrlPageTest(u.toString().toLowerCase());
						p.setPagingPattern("");
					} catch (Exception e1) {

						e1.printStackTrace();
					}
				}
				p.setCssQueryGetListChapter(txtListChapter.getText());
				p.setCssQueryGetChapterTitle(txtChapterTitle.getText().trim());
				p.setCssQueryGetChapterContent(txtChapterContent.getText().trim());
				p.setOverMaxSizePageCountState(
						(Enumeration.OverMaxSizePageCountState) cboPageStateWhenOver.getSelectedItem());
				p.setIsChapterLinkAsolute(chckbxngPathIsAbsoluted.isSelected());
				p.setIsManualGet(chckboxUseForManualGET.isSelected());
				p.setIsEnableChapterSign(chckbxEnableChapterSign.isSelected());
				p.setIsRevertChapterList(chckbxRevertListChapter.isSelected());
				p.setCssFilter(txtCssRemoveContent.getText());
				p.setTextGuide(txtGuide.getText());
				p.setIsForumType(chkForumType.isSelected());
				p.setIsVietNameseHost(chkIsVietNamHost.isSelected());
				p.setIsUseJsoupGet(chkIsUseJsoupGet.isSelected());
				p.setScriptJS(txtScript.getText());
				p.setByPassCloudFlare(chckbxBypassCloudflare.isSelected());
				p.setUseBruteForceMethod(chckbxUseBruteForce.isSelected());

				Config.editHost((PageConfig) cboPageConfigList.getSelectedItem(), p);
				txtLog.append(Messages.getGlobalString("log.editedHost") + p.getPageCode());
				break;
			case DELETE:
				p = new PageConfig(u.getHost().toLowerCase());
				if (JOptionPane.showConfirmDialog(null,
						String.format(Messages.getGlobalString("question.confirmDelete"), u.getHost()),
						Messages.getGlobalString("title.delete"), JOptionPane.YES_NO_CANCEL_OPTION,
						JOptionPane.QUESTION_MESSAGE) == JOptionPane.YES_OPTION) {
					Config.deleteHostByPageCode(p.getPageCode());
					txtLog.append(String.format(Messages.getGlobalString("log.deletedHost"), p.getPageCode()));
				}
				break;
			default:
				break;
			}
		} catch (

		MalformedURLException e1) {
			e1.printStackTrace();
		}

		setLogColorAndActionType(FONT_TYPE.NONE);
		setComponentEnable(false);
		GetListToCombo("");
		// clear filter
		txtFilter.setText("");

		// update combo config host
		Main.updateHostList();
	}

	void setComponentEnable(Boolean b) {
		// reset tabpanel state to default tab 0
		if (!b) {
			tabbedPane.setSelectedIndex(0);
		}
		// clean control
		chckboxUseForManualGET.setSelected(false);
		chckbxEnableChapterSign.setSelected(false);
		chckbxRevertListChapter.setSelected(false);
		chkTestSelectAll.setSelected(false);
		chkForumType.setSelected(false);
		chkIsUseJsoupGet.setSelected(false);
		chkIsVietNamHost.setSelected(false);
		chckbxUseBruteForce.setSelected(false);

		txtChapterContent.setText("");
		txtChapterTitle.setText("");
		txtHost.setText("");
		txtListChapter.setText("");
		txtPagePattern.setText("");
		txtCssRemoveContent.setText("");
		txtGuide.setText("");
		txtCssTestAll.setText("");
		txtScript.setText("");

		// button
		btnEdit.setEnabled(!b);
		btnDelete.setEnabled(!b);
		btnAdd.setEnabled(!b);
		btnRefresh.setEnabled(!b);
		btnDuplicate.setEnabled(!b);

		cboPageConfigList.setEnabled(!b);
		txtFilter.setEnabled(!b);

		btnCancel.setVisible(b);
		btnSave.setVisible(b);

		// control for edit
		chckboxUseForManualGET.setEnabled(b);
		chckbxngPathIsAbsoluted.setEnabled(b);
		chckbxEnableChapterSign.setEnabled(b);
		chckbxRevertListChapter.setEnabled(b);
		chkTestSelectAll.setEnabled(b);
		chkForumType.setEnabled(b);
		chkIsUseJsoupGet.setEnabled(b);
		chkIsVietNamHost.setEnabled(b);
		chckbxBypassCloudflare.setEnabled(b);
		chckbxUseBruteForce.setEnabled(b);

		txtChapterContent.setEnabled(b);
		txtChapterTitle.setEnabled(b);
		txtHost.setEnabled(b);
		txtListChapter.setEnabled(b);
		txtPagePattern.setEnabled(b);
		txtGuide.setEnabled(b);
		txtScript.setEnabled(b);
		txtCssRemoveContent.setEnabled(b);
		txtCssTestAll.setEnabled(b);
		tabbedPane.setEnabled(b);

		btnTestChapterContent.setEnabled(b);
		btnTestChapterTitle.setEnabled(b);
		btnTestListChapter.setEnabled(b);
		btnTestFilter.setEnabled(b);
		btnTestAll.setEnabled(b);

		cboPageStateWhenOver.setEnabled(b);

		PageConfig p = (PageConfig) cboPageConfigList.getSelectedItem();
		switch (actionType) {
		case ADD:
			txtLog.append(Messages.getGlobalString("log.addNewHost"));
			txtCssRemoveContent.setText("[style];form;button;script;");

			txtHost.requestFocus();
			break;
		case EDIT:
		case DUPLICATE:
		case DELETE:
			String logMessage = String.format(Messages.getGlobalString("log.edittingHost"), p.getPageCode());
			if (actionType == FONT_TYPE.DUPLICATE) {
				logMessage = String.format(Messages.getGlobalString("log.duplicateHost"), p.getPageCode());
			} else if (actionType == FONT_TYPE.DELETE) {
				logMessage = String.format(Messages.getGlobalString("log.prepareDeleteHost"), p.getPageCode());
			}
			txtLog.append(logMessage);

			// binding control value
			txtChapterContent.setText(p.getCssQueryGetChapterContent());
			txtChapterTitle.setText(p.getCssQueryGetChapterTitle());
			txtHost.setText(p.getUrlPageTest());
			txtListChapter.setText(p.getCssQueryGetListChapter());
			txtPagePattern.setText(p.getPagingPattern());
			txtCssRemoveContent.setText(p.getCssFilter());
			txtGuide.setText(p.getTextGuide());
			txtScript.setText(p.getScriptJS());

			cboPageStateWhenOver.setSelectedItem(p.getOverMaxSizePageCountState());
			chckbxngPathIsAbsoluted.setSelected(p.getIsChapterLinkAsolute());
			chckboxUseForManualGET.setSelected(p.getIsManualGet());
			chckbxEnableChapterSign.setSelected(p.getIsEnableChapterSign());
			chckbxRevertListChapter.setSelected(p.getIsRevertChapterList());
			chkForumType.setSelected(p.getIsForumType());
			chkIsUseJsoupGet.setSelected(p.getIsUseJsoupGet());
			chkIsVietNamHost.setSelected(p.getIsVietNameseHost());
			chckbxBypassCloudflare.setSelected(p.getByPassCloudFlare());
			chckbxUseBruteForce.setSelected(p.getUseBruteForceMethod());

			txtListChapter.requestFocus();
			break;

		default:
			break;
		}
	}

	/**
	 * set log color and action
	 * 
	 * @param font
	 */
	void setLogColorAndActionType(FONT_TYPE font) {
		switch (font) {
		case NORMAL:
			txtLog.setForeground(Color.WHITE);
		case ADD:
			txtLog.setForeground(Color.GREEN);
			break;
		case DELETE:
			txtLog.setForeground(Color.RED);
			break;
		case EDIT:
			txtLog.setForeground(Color.ORANGE);
			break;
		case DUPLICATE:
			txtLog.setForeground(Color.GREEN);
			break;
		default:
			break;
		}
		txtLog.setText("");
		actionType = font;
	}
}
