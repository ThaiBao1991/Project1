package main;

import java.awt.Component;
import java.awt.EventQueue;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusAdapter;
import java.awt.event.FocusEvent;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.Locale;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSpinner;
import javax.swing.JTextField;
import javax.swing.JTextPane;
import javax.swing.SpinnerNumberModel;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;
import javax.swing.border.EtchedBorder;
import javax.swing.border.TitledBorder;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;

import org.eclipse.wb.swing.FocusTraversalOnArray;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonValue;
import common.Enumeration;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import resource.text.Messages;

public class CopyRightInfo extends JFrame {

	/**
	 * 
	 */
	private static final long serialVersionUID = -4908021877809214828L;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				try {
					CopyRightInfo frame = new CopyRightInfo();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JPanel contentPane;
	private JTextField txtEbookCreator;
	private JTextField txtSource;
	private JTextPane txtInfo, txtConverter;
	public String ebookInfo;
	private JTextField txtAuthor;
	private JTextField txtName;
	private JTextField txtStatus;

	private JButton btnDownloadInit;

	private PreviewHtml preview;

	private Boolean isShowPreview = false;
	private JTextField txtDivideChapterTitle;
	private JSpinner spinnerDivideChapterCount;
	private JCheckBox chckbxUseDiveTable;

	/**
	 * Create the frame.
	 */
	public CopyRightInfo() {

		init();
	}

	public CopyRightInfo(JButton btnDownload) {
		init();
		btnDownloadInit = btnDownload;
		this.ebookInfo = "";
	}

	void init() {
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowOpened(WindowEvent arg0) {

				txtEbookCreator.setText(SettingOption.getString(EnumConfigKey.EBOOKCREATOR, ""));
				txtConverter.setText(SettingOption.getString(EnumConfigKey.CONVERTER, ""));
				txtSource.setText(SettingOption.getString(EnumConfigKey.SOURCE, ""));
				txtAuthor.setText(SettingOption.getString(EnumConfigKey.AUTHOR, ""));
				txtName.setText(SettingOption.getString(EnumConfigKey.EBOOKNAME, ""));
				txtStatus.setText(SettingOption.getString(EnumConfigKey.STATUS, ""));

				// mkbyme - 2018.12.09 setup use 2 TOC config
				Boolean isUseDivideTable = SettingOption.getBoolean(EnumConfigKey.IS_USE_2_LEVEL_FOR_TOC, false);
				chckbxUseDiveTable.setSelected(isUseDivideTable);
				txtDivideChapterTitle.setText(SettingOption.getString(EnumConfigKey.TWO_LEVEL_CHAPTER_TITLE,
						Constant.DEFAULT_TWO_LEVEL_CHAPTER_TITLE));
				spinnerDivideChapterCount.setValue(SettingOption.getInt(EnumConfigKey.TWO_LEVEL_BREAK_CHAPTER_COUNT,
						Constant.DEFAULT_TWO_LEVEL_BREAK_CHAPTER_COUNT));
				String infoString = SettingOption.getString(EnumConfigKey.INFO,
						String.format(Messages.getGlobalString("text.ebookIntro"), CommonValue.getAppName()));

				txtInfo.setText(infoString);

				txtEbookCreator.setFocusable(true);
			}
		});
		setIconImage(Toolkit.getDefaultToolkit().getImage(CopyRightInfo.class.getResource("/resource/box-16.png")));
		setTitle(Messages.getString("CopyRightInfo.this.title")); //$NON-NLS-1$
		setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		setBounds(100, 100, 639, 500);
		contentPane = new JPanel();
		contentPane.setBorder(new EtchedBorder(EtchedBorder.LOWERED, null, null));
		setContentPane(contentPane);

		JScrollPane scrollPane = new JScrollPane();

		JLabel lblEbookCreator = new JLabel(Messages.getString("CopyRightInfo.lblEbookCreator.text")); //$NON-NLS-1$

		JLabel lblConverter = new JLabel(Messages.getString("CopyRightInfo.lblConverter.text")); //$NON-NLS-1$

		JLabel lblSource = new JLabel(Messages.getString("CopyRightInfo.lblSource.text")); //$NON-NLS-1$

		txtEbookCreator = new JTextField();
		txtEbookCreator.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		txtEbookCreator.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent arg0) {
				txtEbookCreator.selectAll();
			}
		});
		txtEbookCreator.setColumns(10);

		txtSource = new JTextField();
		txtSource.setColumns(10);
		txtSource.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent e) {
				txtSource.selectAll();
			}
		});
		txtSource.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		JButton btnDownload = new JButton(Messages.getString("CopyRightInfo.btnDownload.text"));
		btnDownload.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {

				getEbookInfo();
				setVisible(false);
				if (preview != null) {
					preview.setVisible(false);
					preview.dispose();
					preview = null;
				}
				btnDownloadInit.doClick();
			}
		});

		JButton btnSave = new JButton(Messages.getString("CopyRightInfo.btnSave.text")); //$NON-NLS-1$
		btnSave.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				Config.put(EnumConfigKey.EBOOKCREATOR, txtEbookCreator.getText());
				Config.put(EnumConfigKey.CONVERTER, txtConverter.getText());
				Config.put(EnumConfigKey.SOURCE, txtSource.getText());
				Config.put(EnumConfigKey.AUTHOR, txtAuthor.getText());
				Config.put(EnumConfigKey.EBOOKNAME, txtName.getText());
				Config.put(EnumConfigKey.STATUS, txtStatus.getText());
				Config.put(EnumConfigKey.INFO, txtInfo.getText());
				Config.put(EnumConfigKey.IS_USE_2_LEVEL_FOR_TOC, chckbxUseDiveTable.isSelected());
				if (chckbxUseDiveTable.isSelected()) {
					Config.put(EnumConfigKey.TWO_LEVEL_CHAPTER_TITLE, txtDivideChapterTitle.getText().trim());
					Config.put(EnumConfigKey.TWO_LEVEL_BREAK_CHAPTER_COUNT, spinnerDivideChapterCount.getValue());
				}
				Config.saveConfig(Enumeration.ConfigType.Setting);

				btnDownload.doClick();
			}
		});

		JLabel lblIntro = new JLabel(Messages.getString("CopyRightInfo.lblIntro.text")); //$NON-NLS-1$

		JLabel lblAuthor = new JLabel(Messages.getString("CopyRightInfo.lblAuthor.text")); //$NON-NLS-1$

		JLabel lblName = new JLabel(Messages.getString("CopyRightInfo.lblName.text")); //$NON-NLS-1$

		JLabel lblStatus = new JLabel(Messages.getString("CopyRightInfo.lblStatus.text")); //$NON-NLS-1$

		txtAuthor = new JTextField();
		txtAuthor.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent e) {
				txtAuthor.selectAll();
			}
		});
		txtAuthor.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		txtAuthor.setText("");
		txtAuthor.setColumns(10);

		txtName = new JTextField();
		txtName.setText("");
		txtName.setColumns(10);
		txtName.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent e) {
				txtAuthor.selectAll();
			}
		});
		txtName.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		txtStatus = new JTextField();
		txtStatus.setText("");
		txtStatus.setColumns(10);
		txtStatus.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent e) {
				txtStatus.selectAll();
			}
		});
		txtStatus = new JTextField();
		txtStatus.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		JLabel lblcanBeHtml = new JLabel(Messages.getString("CopyRightInfo.lblcanBeHtml.text")); //$NON-NLS-1$
		lblcanBeHtml.setForeground(SystemColor.textHighlight);

		txtInfo = new JTextPane();
		txtInfo.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent e) {
				txtInfo.selectAll();
			}
		});
		txtInfo.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		scrollPane.setViewportView(txtInfo);
		contentPane.setLayout(new FormLayout(
				new ColumnSpec[] { ColumnSpec.decode("2dlu"), ColumnSpec.decode("80px"), ColumnSpec.decode("2dlu"),
						ColumnSpec.decode("238px:grow"), ColumnSpec.decode("2dlu"), ColumnSpec.decode("135px"), },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("55px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("20px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("20px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("20px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("20px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("max(56dlu;default)"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("14px:grow"), RowSpec.decode("14px"), }));

		JButton btnClean = new JButton(Messages.getString("CopyRightInfo.btnClean.text")); //$NON-NLS-1$
		btnClean.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				txtConverter.setText("");
				txtSource.setText("");
				txtInfo.setText("");
				txtAuthor.setText("");
				txtName.setText("");
				txtStatus.setText("");

			}
		});

		JScrollPane scrollPane_1 = new JScrollPane();
		contentPane.add(scrollPane_1, "4, 4, fill, fill");

		txtConverter = new JTextPane();
		txtConverter.setText("");
		txtConverter.addKeyListener(new KeyAdapter() {
			@Override
			public void keyReleased(KeyEvent arg0) {
				showContentToPreview();
			}
		});
		scrollPane_1.setViewportView(txtConverter);
		contentPane.add(btnClean, "6, 6, fill, bottom");

		JButton btnPreview = new JButton(Messages.getString("CopyRightInfo.btnPreview.text")); //$NON-NLS-1$
		btnPreview.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				isShowPreview = !isShowPreview;
				if (isShowPreview) {
					btnPreview.setText(Messages.getString("CopyRightInfo.btnPreview.text.unShow"));
					showContentToPreview();
				} else {
					btnPreview.setText(Messages.getString("CopyRightInfo.btnPreview.text"));
					preview.setVisible(false);
					preview.dispose();
					preview = null;
				}

			}
		});
		contentPane.add(btnPreview, "6, 8, fill, fill");

		JLabel lblDivideTableOf = new JLabel(Messages.getString("CopyRightInfo.lblDivideTableOf.text")); //$NON-NLS-1$
		lblDivideTableOf.setToolTipText(Messages.getString("CopyRightInfo.lblDivideTableOf.toolTipText")); //$NON-NLS-1$
		contentPane.add(lblDivideTableOf, "2, 14, center, center");

		JPanel panel = new JPanel();
		panel.setBorder(new TitledBorder(null, "", TitledBorder.LEADING, TitledBorder.TOP, null, null));
		contentPane.add(panel, "4, 14, fill, fill");
		panel.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, FormSpecs.DEFAULT_COLSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("default:grow"), },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));

		chckbxUseDiveTable = new JCheckBox(Messages.getString("CopyRightInfo.chckbxUseDiveTable.text")); //$NON-NLS-1$
		chckbxUseDiveTable.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				txtDivideChapterTitle.setEnabled(chckbxUseDiveTable.isSelected());
				spinnerDivideChapterCount.setEnabled(chckbxUseDiveTable.isSelected());
				Config.put(EnumConfigKey.IS_USE_2_LEVEL_FOR_TOC, chckbxUseDiveTable.isSelected());
			}
		});
		panel.add(chckbxUseDiveTable, "2, 2, left, fill");

		JLabel lblTitle = new JLabel(Messages.getString("CopyRightInfo.lblTitle.text")); //$NON-NLS-1$
		panel.add(lblTitle, "2, 4, left, default");

		txtDivideChapterTitle = new JTextField();
		txtDivideChapterTitle.addFocusListener(new FocusAdapter() {
			@Override
			public void focusLost(FocusEvent arg0) {
				Config.put(EnumConfigKey.TWO_LEVEL_CHAPTER_TITLE, txtDivideChapterTitle.getText());
			}
		});
		txtDivideChapterTitle.setEnabled(false);
		txtDivideChapterTitle.setText(Messages.getString("CopyRightInfo.textField.text")); //$NON-NLS-1$
		panel.add(txtDivideChapterTitle, "4, 4, fill, default");
		txtDivideChapterTitle.setColumns(10);

		JLabel lblDivideChapterCount = new JLabel(Messages.getString("CopyRightInfo.lblDivideChapterCount.text")); //$NON-NLS-1$
		lblDivideChapterCount.setToolTipText(Messages.getString("CopyRightInfo.lblDivideChapterCount.toolTipText")); //$NON-NLS-1$
		panel.add(lblDivideChapterCount, "2, 6, fill, center");

		spinnerDivideChapterCount = new JSpinner();
		spinnerDivideChapterCount.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				Config.put(EnumConfigKey.TWO_LEVEL_BREAK_CHAPTER_COUNT, spinnerDivideChapterCount.getValue());
			}
		});
		spinnerDivideChapterCount.setEnabled(false);
		spinnerDivideChapterCount.setModel(new SpinnerNumberModel(50, 5, 10000, 1));
		panel.add(spinnerDivideChapterCount, "4, 6, fill, fill");
		contentPane.add(lblcanBeHtml, "2, 17, 3, 1, left, top");
		contentPane.add(lblEbookCreator, "2, 2, right, center");
		contentPane.add(lblConverter, "2, 4, right, center");
		contentPane.add(lblSource, "2, 6, right, center");
		contentPane.add(lblAuthor, "2, 8, right, center");
		contentPane.add(lblStatus, "2, 12, right, center");
		contentPane.add(lblName, "2, 10, right, center");
		contentPane.add(lblIntro, "2, 16, right, top");
		contentPane.add(scrollPane, "4, 16, fill, fill");
		contentPane.add(txtStatus, "4, 12, fill, top");
		contentPane.add(txtName, "4, 10, fill, top");
		contentPane.add(txtAuthor, "4, 8, fill, top");
		contentPane.add(txtSource, "4, 6, fill, top");
		contentPane.add(txtEbookCreator, "4, 2, fill, center");
		contentPane.add(btnDownload, "6, 2, fill, top");
		contentPane.add(btnSave, "6, 4, fill, top");
		setFocusTraversalPolicy(new FocusTraversalOnArray(new Component[] { txtEbookCreator, txtSource, txtAuthor,
				txtName, txtStatus, txtInfo, btnDownload, btnSave, btnClean }));
	}

	/**
	 * get ebook info html content
	 * 
	 * @author mkbyme Oct 15, 2017
	 */
	public void getEbookInfo() {
		ebookInfo = CommonValue.getEbookInfoOpen();

		if (!txtEbookCreator.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookCreatorHTML(txtEbookCreator.getText());
		}
		if (!txtConverter.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookConverterHTML(txtConverter.getText());
		}
		if (!txtSource.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookSourceHTML(txtSource.getText());
		}
		if (!txtAuthor.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookAuthorHTML(txtAuthor.getText());
		}
		if (!txtName.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookStoryNameHTML(txtName.getText());
		}
		if (!txtStatus.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookStatusHTML(txtStatus.getText());
		}
		if (!txtInfo.getText().isEmpty()) {
			ebookInfo += CommonValue.getEbookDescriptionHTML(txtInfo.getText());
		}

		ebookInfo += CommonValue.getEbookInfoClose();
	}

	/**
	 * show live preview
	 */
	public void showContentToPreview() {
		if (isShowPreview) {
			getEbookInfo();

			StringBuilder sb = new StringBuilder();
			sb.append(CommonValue.getHtmlOpenString(txtName.getText()));
			sb.append(ebookInfo);
			sb.append(CommonValue.getHtmlCloseString());
			// show preview
			if (preview == null) {
				preview = new PreviewHtml();
			}
			preview.loadHtmlContent(sb.toString());

			if (!preview.isShowing()) {
				preview.setBounds(getBounds().x + getWidth(), getBounds().y, 600, 450);
				preview.setAlwaysOnTop(true);
				preview.setFocusable(false);
				preview.setVisible(true);
			}

		}
	}

}
