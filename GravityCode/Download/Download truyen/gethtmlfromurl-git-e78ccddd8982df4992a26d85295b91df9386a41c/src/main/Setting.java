package main;

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.EventQueue;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.Locale;
import java.util.ResourceBundle;

import javax.swing.ButtonGroup;
import javax.swing.GroupLayout;
import javax.swing.GroupLayout.Alignment;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JScrollPane;
import javax.swing.JSpinner;
import javax.swing.JTabbedPane;
import javax.swing.LayoutStyle.ComponentPlacement;
import javax.swing.SpinnerNumberModel;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.border.TitledBorder;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import javax.swing.text.Document;
import javax.swing.text.html.HTMLEditorKit;
import javax.swing.text.html.StyleSheet;

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

public class Setting extends JDialog {

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
					Setting frame = new Setting();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JPanel contentPane;
	ButtonGroup rdbGroup, rdbtLanguage;
	JRadioButton rdbtnEnglish;
	JRadioButton rdbtnVietnamese;
	JPanel panel_1;
	private JLabel lblNote;
	private JSpinner spinner, spinnerLineSpacing, spinner_TimeOut, spinner_SleepTime;
	Boolean fisrt = true;
	private JScrollPane scrollPane;
	String txtTest = "<html><body style=\"line-height:3em;\"><h3>The standard Lorem Ipsum passage, used since the 1500s</h3>"
			+ "<p>\"Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
			+ "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
			+ "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
			+ "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum "
			+ "dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, "
			+ "sunt in culpa qui officia deserunt mollit anim id est laborum.\"</p><h3>Section 1.10.32 "
			+ "of \"de Finibus Bonorum et Malorum\", written by Cicero in 45 BC</h3><p>\"Sed ut perspiciatis "
			+ "unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, "
			+ "eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. "
			+ "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia "
			+ "consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.</p></body></html>";
	final float POINT_TO_EM = 0.0833333333333333F;
	private JEditorPane txtTestLineSpacing;
	private JLabel lblapplyForNew;

	private JLabel lblHoverMouseToMoreInfoTips;
	private JPanel panel;
	private JCheckBox chkShowChapterHasImageContent;

	/**
	 * Create the frame.
	 */
	public Setting() {
		initizle();
	}

	void initizle() {

		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));

		setIconImage(Toolkit.getDefaultToolkit().getImage(Setting.class.getResource("/resource/box-16.png")));
		setResizable(false);
		setBounds(new Rectangle(0, 0, 470, 130));
		setMaximumSize(new Dimension(400, 200));
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			e2.printStackTrace();
		}
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowOpened(WindowEvent arg0) {
				readConfig();
			}
		});
		setTitle(ResourceBundle.getBundle("resource.text.messages").getString("Setting.this.title")); //$NON-NLS-1$ //$NON-NLS-2$
		setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
		setBounds(100, 100, 444, 401);
		contentPane = new JPanel();
		contentPane.setBorder(null);
		setContentPane(contentPane);
		rdbGroup = new ButtonGroup();

		JTabbedPane tabbedPane = new JTabbedPane(SwingConstants.TOP);
		GroupLayout gl_contentPane = new GroupLayout(contentPane);
		gl_contentPane.setHorizontalGroup(gl_contentPane.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_contentPane.createSequentialGroup().addContainerGap()
						.addComponent(tabbedPane, GroupLayout.DEFAULT_SIZE, 521, Short.MAX_VALUE).addContainerGap()));
		gl_contentPane.setVerticalGroup(gl_contentPane.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_contentPane.createSequentialGroup().addContainerGap()
						.addComponent(tabbedPane, GroupLayout.PREFERRED_SIZE, 214, Short.MAX_VALUE).addContainerGap()));

		JPanel panel_3 = new JPanel();
		tabbedPane.addTab(ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_3.title"), null, //$NON-NLS-1$ //$NON-NLS-2$
				panel_3, null);
		panel_3.setLayout(
				new FormLayout(new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), },
						new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("default:grow"),
								FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		panel_1 = new JPanel();
		panel_3.add(panel_1, "2, 2");
		panel_1.setDoubleBuffered(false);
		panel_1.setBorder(new TitledBorder(null,
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_1.borderTitle_1"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.CENTER, TitledBorder.TOP, null, null));

		rdbtnVietnamese = new JRadioButton(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.rdbtnVietnamese.text"));
		rdbtnVietnamese.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent e) {
				if (rdbtnVietnamese.isSelected()) {
					Config.put(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE);
					writeConfig();
				}
			}
		});

		rdbtnEnglish = new JRadioButton(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.rdbtnEnglish.text")); //$NON-NLS-1$ //$NON-NLS-2$
		rdbtnEnglish.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent e) {
				if (rdbtnEnglish.isSelected()) {
					Config.put(EnumConfigKey.LANGUAGE, "en");
					writeConfig();
				}
			}
		});
		rdbtLanguage = new ButtonGroup();
		rdbtLanguage.add(rdbtnEnglish);
		rdbtLanguage.add(rdbtnVietnamese);

		lblNote = new JLabel(ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblNote.text")); //$NON-NLS-1$ //$NON-NLS-2$
		lblNote.setForeground(Color.LIGHT_GRAY);

		GroupLayout gl_panel_1 = new GroupLayout(panel_1);
		gl_panel_1.setHorizontalGroup(gl_panel_1.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_panel_1.createSequentialGroup().addContainerGap()
						.addGroup(gl_panel_1.createParallelGroup(Alignment.LEADING).addComponent(rdbtnVietnamese)
								.addComponent(rdbtnEnglish).addComponent(lblNote))
						.addContainerGap(18, Short.MAX_VALUE)));
		gl_panel_1.setVerticalGroup(gl_panel_1.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_panel_1.createSequentialGroup().addComponent(rdbtnVietnamese)
						.addPreferredGap(ComponentPlacement.RELATED).addComponent(rdbtnEnglish)
						.addPreferredGap(ComponentPlacement.RELATED).addComponent(lblNote)
						.addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)));
		panel_1.setLayout(gl_panel_1);

		JPanel panel_2 = new JPanel();
		panel_3.add(panel_2, "2, 4, fill, fill");
		panel_2.setBorder(new TitledBorder(null,
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_2.borderTitle_1"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.CENTER, TitledBorder.TOP, null, null));

		JLabel lblMaxConnection = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblMaxConnection.text")); //$NON-NLS-1$ //$NON-NLS-2$
		lblMaxConnection.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblMaxConnection.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$

		spinner = new JSpinner();
		lblMaxConnection.setLabelFor(spinner);
		spinner.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.spinner.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		spinner.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent e) {
				Config.put(EnumConfigKey.MAXCONNECTION, (int) spinner.getValue());
				writeConfig();
			}
		});

		spinner.setModel(new SpinnerNumberModel(1, 1, 32, 1));

		JLabel lblSleepTime = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblSleepTime.text")); //$NON-NLS-1$ //$NON-NLS-2$
		lblSleepTime.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblSleepTime.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$

		spinner_SleepTime = new JSpinner();
		lblSleepTime.setLabelFor(spinner_SleepTime);
		spinner_SleepTime.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.spinner_SleepTime.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		spinner_SleepTime.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent arg0) {
				CommonValue.updateDownloadConfig((int) spinner_TimeOut.getValue(), (int) spinner_SleepTime.getValue());
			}
		});
		spinner_SleepTime.setModel(new SpinnerNumberModel(new Integer(25), new Integer(10), null, new Integer(5)));

		JLabel lblTimeOut = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblTimeOut.text")); //$NON-NLS-1$ //$NON-NLS-2$
		lblTimeOut.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblTimeOut.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$

		spinner_TimeOut = new JSpinner();
		lblTimeOut.setLabelFor(spinner_TimeOut);
		spinner_TimeOut.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.spinner_TimeOut.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		spinner_TimeOut.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent e) {
				CommonValue.updateDownloadConfig((int) spinner_TimeOut.getValue(), (int) spinner_SleepTime.getValue());
			}
		});
		spinner_TimeOut.setModel(new SpinnerNumberModel(new Integer(30), new Integer(10), null, new Integer(5)));
		panel_2.setLayout(new FormLayout(
				new ColumnSpec[] { ColumnSpec.decode("16px"), ColumnSpec.decode("156px"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("106px:grow"), },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));
		panel_2.add(lblSleepTime, "2, 4, fill, center");
		panel_2.add(spinner_SleepTime, "4, 4, fill, top");
		panel_2.add(lblTimeOut, "2, 6, fill, center");
		panel_2.add(spinner_TimeOut, "4, 6, fill, top");
		panel_2.add(lblMaxConnection, "2, 2, left, center");
		panel_2.add(spinner, "4, 2, fill, top");

		chkShowChapterHasImageContent = new JCheckBox(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.chckbxShowPageHas.text")); //$NON-NLS-1$ //$NON-NLS-2$
		chkShowChapterHasImageContent.addChangeListener(new ChangeListener() {
			public void stateChanged(ChangeEvent arg0) {
				// save option
				Config.put(Enumeration.EnumConfigKey.IS_SHOW_PAGE_HAS_IMAGE,
						chkShowChapterHasImageContent.isSelected());
				Config.saveConfig(Enumeration.ConfigType.Setting);
			}
		});
		chkShowChapterHasImageContent.setToolTipText(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.chckbxShowPageHas.toolTipText")); //$NON-NLS-1$ //$NON-NLS-2$
		panel_2.add(chkShowChapterHasImageContent, "4, 8");

		lblapplyForNew = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblapplyForNew.text")); //$NON-NLS-1$ //$NON-NLS-2$
		lblapplyForNew.setForeground(Color.LIGHT_GRAY);
		panel_2.add(lblapplyForNew, "2, 10");
		panel_2.setFocusTraversalPolicy(new FocusTraversalOnArray(new Component[] { lblMaxConnection, spinner,
				lblSleepTime, spinner_SleepTime, lblTimeOut, spinner_TimeOut, lblapplyForNew }));

		lblHoverMouseToMoreInfoTips = new JLabel(ResourceBundle.getBundle("resource.text.messages") //$NON-NLS-1$
				.getString("Setting.lblHoverMouseToMoreInfoTips.text")); //$NON-NLS-1$
		lblHoverMouseToMoreInfoTips.setForeground(Color.GRAY);
		panel_3.add(lblHoverMouseToMoreInfoTips, "2, 6");
		panel_3.setFocusTraversalPolicy(new FocusTraversalOnArray(new Component[] { panel_1, rdbtnVietnamese,
				rdbtnEnglish, lblNote, panel_2, lblMaxConnection, spinner, lblSleepTime, spinner_SleepTime, lblTimeOut,
				spinner_TimeOut, lblapplyForNew, lblHoverMouseToMoreInfoTips }));

		JPanel panel_4 = new JPanel();
		tabbedPane.addTab(ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_4.title"), null, //$NON-NLS-1$ //$NON-NLS-2$
				panel_4, null);
		panel_4.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"),
						FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("default:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		JLabel lblLineSpacing = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblLineSpacing.text")); //$NON-NLS-1$ //$NON-NLS-2$
		panel_4.add(lblLineSpacing, "2, 2");

		spinnerLineSpacing = new JSpinner();
		spinnerLineSpacing.addChangeListener(new ChangeListener() {
			@Override
			public void stateChanged(ChangeEvent arg0) {

				int point = (int) spinnerLineSpacing.getValue();

				HTMLEditorKit editor = new HTMLEditorKit();
				txtTestLineSpacing.setEditorKit(editor);
				StyleSheet styleSheet = editor.getStyleSheet();

				styleSheet.addRule("body{line-height: " + point + "pt;");

				Config.put(EnumConfigKey.LINE_HEIGHT, point);
				writeConfig();
				Document document = editor.createDefaultDocument();
				txtTestLineSpacing.setDocument(document);
				txtTestLineSpacing.setText(txtTest);

			}
		});
		spinnerLineSpacing.setModel(new SpinnerNumberModel(16, 5, 30, 1));
		panel_4.add(spinnerLineSpacing, "4, 2");

		JLabel lblResult = new JLabel(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblResult.text")); //$NON-NLS-1$ //$NON-NLS-2$
		panel_4.add(lblResult, "2, 4");

		scrollPane = new JScrollPane();
		panel_4.add(scrollPane, "2, 6, 3, 1, fill, fill");

		txtTestLineSpacing = new JEditorPane();
		txtTestLineSpacing.setEditable(false);
		txtTestLineSpacing.setContentType(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.txtTestLineSpacing.contentType")); //$NON-NLS-1$ //$NON-NLS-2$
		txtTestLineSpacing.setText(txtTest);
		scrollPane.setViewportView(txtTestLineSpacing);

		panel = new JPanel();
		tabbedPane.addTab(ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel.title"), null, //$NON-NLS-1$ //$NON-NLS-2$
				panel, null);
		panel.setLayout(
				new FormLayout(new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), },
						new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("default:grow"), }));

		JPanel panel_5 = new JPanel();
		panel_5.setBorder(new TitledBorder(null,
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.panel_5.borderTitle"), //$NON-NLS-1$ //$NON-NLS-2$
				TitledBorder.LEADING, TitledBorder.TOP, null, null));
		panel.add(panel_5, "2, 2, fill, fill");
		panel_5.setLayout(new FormLayout(new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC, FormSpecs.DEFAULT_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, }));

		JButton btnReopenAllWarning = new JButton(
				ResourceBundle.getBundle("resource.text.messages").getString("Setting.btnReopenAllWarning.text")); //$NON-NLS-1$ //$NON-NLS-2$
		btnReopenAllWarning.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				// reopen all warning
				Config.put(EnumConfigKey.SHOW_TIPS_ON_DOWNLOAD_FAILED, true);
				JOptionPane.showMessageDialog(null, Messages.getGlobalString("message.reOpenAllWarningSuccess"));
			}
		});
		panel_5.add(btnReopenAllWarning, "2, 2");

		contentPane.setLayout(gl_contentPane);
	}

	void readConfig() {
		int maxConnection = SettingOption.getInt(EnumConfigKey.MAXCONNECTION, Constant.DEFAULT_MAX_CONNECTION);
		int lineHeight = 16;
		int timeout = 60, sleepTime = 30;

		try {
			lineHeight = SettingOption.getInt(EnumConfigKey.LINE_HEIGHT, Constant.DEFAULT_LINE_HEIGH);
			timeout = SettingOption.getInt(EnumConfigKey.TIME_OUT, Constant.DEFAULT_TIME_OUT);
			sleepTime = SettingOption.getInt(EnumConfigKey.SLEEP_TIME, Constant.DEFAULT_SLEEP_TIME);
			chkShowChapterHasImageContent
					.setSelected(SettingOption.getBoolean(EnumConfigKey.IS_SHOW_PAGE_HAS_IMAGE, true));
		} catch (Exception e) {

		}
		switch (SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)) {
		case "vi":
			rdbtnVietnamese.setSelected(true);
			break;
		case "en":
			rdbtnEnglish.setSelected(true);
		}
		spinner.setValue(maxConnection);
		spinnerLineSpacing.setValue(lineHeight);
		spinner_TimeOut.setValue(timeout);
		spinner_SleepTime.setValue(sleepTime);
	}

	void writeConfig() {

		Config.saveConfig(Enumeration.ConfigType.Setting);
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		setTitle(ResourceBundle.getBundle("resource.text.messages").getString("Setting.this.title"));
		rdbtnVietnamese
				.setText(ResourceBundle.getBundle("resource.text.messages").getString("Setting.rdbtnVietnamese.text"));

		lblNote.setText(ResourceBundle.getBundle("resource.text.messages").getString("Setting.lblNote.text"));
		rdbtnEnglish.setText(ResourceBundle.getBundle("resource.text.messages").getString("Setting.rdbtnEnglish.text"));

		fisrt = false;
	}
}
