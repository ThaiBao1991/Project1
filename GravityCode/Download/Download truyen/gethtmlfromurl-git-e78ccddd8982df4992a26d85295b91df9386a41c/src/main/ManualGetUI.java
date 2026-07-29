package main;

import java.awt.Color;
import java.awt.Component;
import java.awt.Cursor;
import java.awt.EventQueue;
import java.awt.FlowLayout;
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
import java.util.Locale;

import javax.swing.AbstractAction;
import javax.swing.GroupLayout;
import javax.swing.GroupLayout.Alignment;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JProgressBar;
import javax.swing.JScrollPane;
import javax.swing.JSeparator;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.KeyStroke;
import javax.swing.LayoutStyle.ComponentPlacement;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.border.EmptyBorder;
import javax.swing.border.TitledBorder;
import javax.swing.event.UndoableEditEvent;
import javax.swing.event.UndoableEditListener;
import javax.swing.filechooser.FileNameExtensionFilter;
import javax.swing.text.Document;
import javax.swing.undo.CannotRedoException;
import javax.swing.undo.CannotUndoException;
import javax.swing.undo.UndoManager;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.Enumeration;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import models.PageConfig;
import resource.text.Messages;
import thread.TManual;

public class ManualGetUI extends JFrame {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	int isHelpShowHitCount = 0;

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
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				try {
					ManualGetUI frame = new ManualGetUI();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private JPanel contentPane;
	JProgressBar progressBar = new JProgressBar();
	JButton btnDownload = new JButton(Messages.getString("ManualGetUI.btnDownload.text")); //$NON-NLS-1$
	JButton btnCancel = new JButton(Messages.getString("ManualGetUI.btnCancel.text")); //$NON-NLS-1$
	JLabel lblStatus = new JLabel(Messages.getString("ManualGetUI.lblNone.text")); //$NON-NLS-1$
	JLabel lblCount = new JLabel(Messages.getString("ManualGetUI.lblCount.text")); //$NON-NLS-1$
	JTextArea txtInput;
	public JTextArea txtLog;
	JComboBox<PageConfig> comboBox;
	JButton btnResume;
	TManual threadMannualGet;
	JPopupMenu popupMenu;
	JButton btnHelp;
	PageConfig p;
	JCheckBox chkboxSplitFile;
	JCheckBox chckbxDownloadWithSelected;

	CopyRightInfo cri;
	private JTextField txtFilter;

	/**
	 * Create the frame.
	 */
	public ManualGetUI() {

		initlize();
	}

	public ManualGetUI(String pageCode) {
		initlize();
		PageConfig check = new PageConfig(pageCode.toLowerCase().trim());
		int size = comboBox.getItemCount();
		for (int i = 0; i < size; i++) {
			if (comboBox.getItemAt(i).equals(check)) {
				comboBox.setSelectedIndex(i);
				break;
			}
		}
	}

	void enableForm(Boolean b) {
		btnDownload.setEnabled(b);
		btnCancel.setEnabled(!b);
	}

	/*
	 * Load pageconfig from ghfuConfig.data to combobox with filter
	 */
	void getListToCombo(String filterChain) {
		filterChain = filterChain.replaceAll("(https?:\\/\\/)|(\\/.+$)", "").toLowerCase();
		comboBox.removeAllItems();
		Integer count = 0;
		if (filterChain.length() < 3) {
			for (PageConfig pageConfig : Config.getAllHostConfig()) {
				if (pageConfig.getIsManualGet()) {
					comboBox.addItem(pageConfig);
					count++;
				}
			}
		} else {
			for (PageConfig pageConfig : Config.getAllHostConfig()) {
				if (pageConfig.getIsManualGet() && pageConfig.getPageCode().toLowerCase().contains(filterChain)) {
					comboBox.addItem(pageConfig);
					count++;
				}
			}
		}
		lblCount.setText(comboBox.getItemCount() + " Host");
	}

	void initlize() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowClosing(WindowEvent arg0) {
				if (!btnDownload.isEnabled()) {
					int confirm = JOptionPane.showOptionDialog(null, Messages.getGlobalString("warning.inDownloading"),
							Messages.getGlobalString("title.Downloading"), JOptionPane.YES_NO_OPTION,
							JOptionPane.QUESTION_MESSAGE, null,
							new String[] { Messages.getGlobalString("yes"), Messages.getGlobalString("no") },
							Messages.getGlobalString("no"));
					if (confirm == JOptionPane.YES_OPTION) {
						threadMannualGet.cancel();
						arg0.getWindow().dispose();
					}

				} else {
					arg0.getWindow().dispose();
				}
			}
		});
		addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent e) {
				if (e.isPopupTrigger()) {
					popupMenu.show(e.getComponent(), e.getX(), e.getY());
				}
			}
		});
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));

		setIconImage(Toolkit.getDefaultToolkit().getImage(ManualGetUI.class.getResource("/resource/box-16.png")));
		setTitle(Messages.getString("ManualGetUI.this.title")); //$NON-NLS-1$
		setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}

		setBounds(100, 100, 691, 560);

		popupMenu = new JPopupMenu();
		addPopup(this, popupMenu);

		JMenuItem mntmPasteHtml = new JMenuItem(Messages.getString("ManualGetUI.mntmPasteHtml.text")); //$NON-NLS-1$
		mntmPasteHtml.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				try {

					txtInput.setText(Toolkit.getDefaultToolkit().getSystemClipboard().getData(DataFlavor.stringFlavor)
							.toString());
				} catch (HeadlessException | UnsupportedFlavorException | IOException e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
				}
			}
		});
		mntmPasteHtml.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Paste-16.png")));
		popupMenu.add(mntmPasteHtml);

		JMenuItem mntmDownload = new JMenuItem(Messages.getString("ManualGetUI.mntmDownload.text")); //$NON-NLS-1$
		mntmDownload.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				btnDownload.doClick();
			}
		});

		JSeparator separator = new JSeparator();
		popupMenu.add(separator);
		mntmDownload.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Down-16.png")));
		popupMenu.add(mntmDownload);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		setContentPane(contentPane);

		JPanel panel = new JPanel();
		panel.setBorder(new TitledBorder(null, Messages.getString("ManualGetUI.panel.borderTitle"), //$NON-NLS-1$
				TitledBorder.LEADING, TitledBorder.TOP, null, null));

		JPanel panel_1 = new JPanel();
		panel_1.setBorder(new TitledBorder(null, Messages.getString("ManualGetUI.panel_1.borderTitle"),
				TitledBorder.LEADING, TitledBorder.TOP, null, null));
		panel_1.setLayout(new GridLayout(0, 1, 0, 0));

		JScrollPane scrollPane = new JScrollPane();
		panel_1.add(scrollPane);

		txtLog = new JTextArea();
		txtLog.setFont(new Font("SansSerif", Font.PLAIN, 11));
		txtLog.setEditable(false);
		txtLog.setCursor(Cursor.getPredefinedCursor(Cursor.TEXT_CURSOR));
		txtLog.setBackground(Color.GRAY);
		txtLog.setForeground(new Color(0, 255, 0));
		txtLog.setLineWrap(true);
		scrollPane.setViewportView(txtLog);
		GroupLayout gl_contentPane = new GroupLayout(contentPane);
		gl_contentPane.setHorizontalGroup(gl_contentPane.createParallelGroup(Alignment.LEADING)
				.addComponent(panel, GroupLayout.DEFAULT_SIZE, 665, Short.MAX_VALUE)
				.addComponent(panel_1, GroupLayout.DEFAULT_SIZE, 665, Short.MAX_VALUE));
		gl_contentPane.setVerticalGroup(gl_contentPane.createParallelGroup(Alignment.TRAILING)
				.addGroup(gl_contentPane.createSequentialGroup()
						.addComponent(panel, GroupLayout.DEFAULT_SIZE, 382, Short.MAX_VALUE)
						.addPreferredGap(ComponentPlacement.RELATED)
						.addComponent(panel_1, GroupLayout.PREFERRED_SIZE, 137, GroupLayout.PREFERRED_SIZE)));

		JScrollPane scrollPane_1 = new JScrollPane();
		scrollPane_1
				.setBorder(new TitledBorder(null, "HTML (CTRL+V)", TitledBorder.LEFT, TitledBorder.TOP, null, null));

		btnResume = new JButton(Messages.getString("ManualGetUI.btnResumeretry.text")); //$NON-NLS-1$
		btnResume.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				threadMannualGet.start();
				btnResume.setEnabled(false);
			}
		});
		btnResume.setEnabled(false);

		btnHelp = new JButton(Messages.getString("ManualGetUI.btnHelp.text")); //$NON-NLS-1$
		btnHelp.setHorizontalAlignment(SwingConstants.LEFT);
		btnHelp.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {

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

		});
		btnHelp.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/help-desk-icon.png")));
		btnHelp.setBorder(null);
		btnHelp.setContentAreaFilled(false);
		btnDownload.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (txtInput.getText().isEmpty()) {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.pleaseInputContent"));
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

				String defaultFileName = "";
				if (txtInput.getText().contains("<title>")) {
					int i1 = txtInput.getText().indexOf("<title>");
					int i2 = txtInput.getText().indexOf("</title>");
					defaultFileName = txtInput.getText().substring(i1 + 7, i2);
					defaultFileName = defaultFileName.replaceAll("[\\|\\\\\\/\\;\\:\\\"\\*\\<\\>\\?]+", " ");
				}
				try {
					// handing path -> fileName
					if (defaultFileName != "") {
						String recentFolder = SettingOption.getString(EnumConfigKey.RECENT_FOLDER,
								Constant.DEFAULT_RECENT_FOLDER) + File.separator + defaultFileName;
						jfc.setSelectedFile(new File(recentFolder));
					}
				} catch (Exception e) {
					e.printStackTrace();
					jfc.setSelectedFile(new File(File.listRoots()[1] + File.separator + defaultFileName));
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
				// save recent folder;
				Config.put(EnumConfigKey.RECENT_FOLDER, jfc.getSelectedFile().getParentFile().getPath());
				Config.saveConfig(Enumeration.ConfigType.Setting);

				txtLog.setText("");

				// Download Options
				// Download Range
				if (chckbxDownloadWithSelected.isSelected()) {
					DownloadRange.visiable = true;
					chckbxDownloadWithSelected.setSelected(false);
				}

				threadMannualGet = new TManual(btnCancel, btnDownload, btnResume, txtInput.getText(), path, lblStatus,
						txtLog, progressBar, (PageConfig) comboBox.getSelectedItem(), cri != null ? cri.ebookInfo : "",
						chkboxSplitFile.isSelected());

				threadMannualGet.start();
			}
		});
		btnCancel.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				threadMannualGet.cancel();
				btnResume.setEnabled(true);
			}
		});

		txtInput = new JTextArea();
		txtInput.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent e) {
				if (e.isPopupTrigger()) {
					popupMenu.show(e.getComponent(), e.getX(), e.getY());
				}
			}
		});
		txtInput.setWrapStyleWord(true);
		txtInput.setLineWrap(true);
		txtInput.setFont(new Font("SansSerif", Font.PLAIN, 11));
		txtInput.setBackground(Color.WHITE);
		txtInput.setForeground(SystemColor.textHighlight);

		// Undo,Redo
		final UndoManager undo = new UndoManager();
		Document doc = txtInput.getDocument();
		doc.addUndoableEditListener(new UndoableEditListener() {
			@Override
			public void undoableEditHappened(UndoableEditEvent evt) {
				undo.addEdit(evt.getEdit());
			}
		});

		txtInput.getActionMap().put("Undo", new AbstractAction("Undo") {
			private static final long serialVersionUID = 1L;

			@Override
			public void actionPerformed(ActionEvent evt) {
				try {
					if (undo.canUndo()) {
						undo.undo();
					}
				} catch (CannotUndoException e) {
				}
			}
		});

		txtInput.getInputMap().put(KeyStroke.getKeyStroke("control Z"), "Undo");

		txtInput.getActionMap().put("Redo", new AbstractAction("Redo") {

			private static final long serialVersionUID = 1L;

			@Override
			public void actionPerformed(ActionEvent evt) {
				try {
					if (undo.canRedo()) {
						undo.redo();
					}
				} catch (CannotRedoException e) {
				}
			}
		});

		txtInput.getInputMap().put(KeyStroke.getKeyStroke("control R"), "Redo");

		scrollPane_1.setViewportView(txtInput);

		JPanel panel_5 = new JPanel();
		FlowLayout flowLayout_1 = (FlowLayout) panel_5.getLayout();
		flowLayout_1.setAlignment(FlowLayout.LEFT);
		flowLayout_1.setVgap(1);
		flowLayout_1.setHgap(1);
		scrollPane_1.setColumnHeaderView(panel_5);

		JButton btnSearchReplace = new JButton(Messages.getString("ManualGetUI.btnSearchReplace.text"));
		btnSearchReplace.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				FindAndReplace far = new FindAndReplace(txtInput);
				far.setVisible(true);
			}
		});
		btnSearchReplace.setToolTipText(Messages.getString("ManualGetUI.btnSearchReplace.toolTipText")); //$NON-NLS-1$
		btnSearchReplace.setBorderPainted(false);
		btnSearchReplace.setMargin(new Insets(1, 1, 1, 1));
		btnSearchReplace.setContentAreaFilled(false);
		btnSearchReplace.setActionCommand(Messages.getString("ManualGetUI.btnSearchReplace.actionCommand")); //$NON-NLS-1$
		btnSearchReplace.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Find and Replace-16.png")));
		panel_5.add(btnSearchReplace);

		JButton btnUndo = new JButton(Messages.getString("ManualGetUI.btnUndo.text_1")); //$NON-NLS-1$
		btnUndo.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (undo.canUndo()) {
					undo.undo();
				}
			}
		});
		btnUndo.setMargin(new Insets(1, 1, 1, 1));
		btnUndo.setContentAreaFilled(false);
		btnUndo.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Undo-16.png")));
		btnUndo.setToolTipText(Messages.getString("ManualGetUI.btnUndo.toolTipText_1")); //$NON-NLS-1$
		panel_5.add(btnUndo);

		JButton btnRedo = new JButton(Messages.getString("ManualGetUI.btnRedi.text"));
		btnRedo.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (undo.canRedo()) {
					undo.redo();
				}
			}
		});
		btnRedo.setToolTipText(Messages.getString("ManualGetUI.btnRedo.toolTipText")); //$NON-NLS-1$
		btnRedo.setMargin(new Insets(1, 1, 1, 1));
		btnRedo.setContentAreaFilled(false);
		btnRedo.setBorderPainted(false);
		btnRedo.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Redo-16.png")));
		panel_5.add(btnRedo);

		JButton btnPasteLink = new JButton(Messages.getString("ManualGetUI.btnPasteLink.text")); //$NON-NLS-1$
		btnPasteLink.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				try {

					String link = Toolkit.getDefaultToolkit().getSystemClipboard().getData(DataFlavor.stringFlavor)
							.toString();
					if (link.length() < 2000) {
						txtInput.append("<a href=\"" + link + "\">Paste Link</a>\r\n");
					}

				} catch (HeadlessException | UnsupportedFlavorException | IOException e1) {
					e1.printStackTrace();
				}
			}
		});
		btnPasteLink.setToolTipText(Messages.getString("ManualGetUI.btnPasteLink.toolTipText")); //$NON-NLS-1$
		btnPasteLink.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Link-16.png")));
		btnPasteLink.setMargin(new Insets(1, 1, 1, 1));
		btnPasteLink.setContentAreaFilled(false);
		panel_5.add(btnPasteLink);

		JButton btnCleanText = new JButton(Messages.getString("ManualGetUI.btnCleanText.text")); //$NON-NLS-1$
		btnCleanText.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				txtInput.setText("");
				txtInput.requestFocus();

			}
		});
		btnCleanText.setToolTipText(Messages.getString("ManualGetUI.btnCleanText.toolTipText")); //$NON-NLS-1$
		btnCleanText.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Erase-16.png")));
		btnCleanText.setMargin(new Insets(1, 1, 1, 1));
		btnCleanText.setContentAreaFilled(false);
		panel_5.add(btnCleanText);
		panel.setLayout(new FormLayout(
				new ColumnSpec[] { ColumnSpec.decode("2dlu"), ColumnSpec.decode("80px"), ColumnSpec.decode("2dlu"),
						ColumnSpec.decode("442px:grow"), FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("112px"), },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("16dlu"), RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("top:69px"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("125px:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("23px"), FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("23px"), }));

		JLabel lblFilterHost = new JLabel(Messages.getString("ManualGetUI.lblFilterHost.text")); //$NON-NLS-1$
		panel.add(lblFilterHost, "2, 2, right, fill");

		JPanel panel_6 = new JPanel();
		panel.add(panel_6, "4, 2, fill, top");
		panel_6.setLayout(
				new FormLayout(new ColumnSpec[] { ColumnSpec.decode("default:grow"), ColumnSpec.decode("16dlu"), },
						new RowSpec[] { FormSpecs.DEFAULT_ROWSPEC, }));

		txtFilter = new JTextField();
		txtFilter.addInputMethodListener(new InputMethodListener() {
			public void caretPositionChanged(InputMethodEvent arg0) {
				if (txtFilter.getText().isEmpty() && !txtFilter.isFocusOwner()) {
					txtFilter.setText(Messages.getString("ManualGetUI.txtFilter.text"));
					txtFilter.setForeground(Color.GRAY);
				}
			}

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
					txtFilter.requestFocus(true);
				}
			}
		});
		txtFilter.addFocusListener(new FocusAdapter() {
			@Override
			public void focusGained(FocusEvent e) {
				if (txtFilter.getText().equals(Messages.getString("ManualGetUI.txtFilter.text"))) {
					txtFilter.setText("");
					txtFilter.setForeground(Color.BLACK);
				}
			}

			@Override
			public void focusLost(FocusEvent e) {
				if (txtFilter.getText().isEmpty()) {
					txtFilter.setText(Messages.getString("ManualGetUI.txtFilter.text"));
					txtFilter.setForeground(Color.GRAY);
				}
			}
		});
		txtFilter.setForeground(Color.GRAY);
		txtFilter.setToolTipText(Messages.getString("")); //$NON-NLS-1$
		txtFilter.setText(Messages.getString("ManualGetUI.txtFilter.text")); //$NON-NLS-1$
		panel_6.add(txtFilter, "1, 1, fill, fill");
		txtFilter.setColumns(10);

		JButton btnClear = new JButton("");
		btnClear.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				txtFilter.setText("");
				getListToCombo("");
			}
		});
		btnClear.setIcon(new ImageIcon(ManualGetUI.class.getResource("/resource/Delete-16.png")));
		panel_6.add(btnClear, "2, 1, fill, fill");

		comboBox = new JComboBox<>();
		comboBox.addItemListener(new ItemListener() {
			@Override
			public void itemStateChanged(ItemEvent e) {
				p = (PageConfig) comboBox.getSelectedItem();
				if (p != null) {
					btnHelp.setText(Messages.getString("ManualGetUI.btnHelp.text") + "\"" + p.getPageCode() + "\"");
				}
			}
		});

		lblCount.setFont(new Font("Tahoma", Font.BOLD, 13));
		lblCount.setForeground(new Color(0, 128, 0));
		panel.add(lblCount, "2, 3, right, default");
		panel.add(comboBox, "4, 3, fill, center");

		JPanel panel_3 = new JPanel();
		panel.add(panel_3, "4, 7, fill, fill");
		panel_3.setLayout(new FormLayout(
				new ColumnSpec[] { ColumnSpec.decode("226px"), FormSpecs.RELATED_GAP_COLSPEC,
						ColumnSpec.decode("187px:grow"), },
				new RowSpec[] { FormSpecs.LINE_GAP_ROWSPEC, RowSpec.decode("63px:grow"),
						FormSpecs.LINE_GAP_ROWSPEC, }));

		JPanel panel_2 = new JPanel();
		panel_3.add(panel_2, "1, 2, fill, top");
		panel_2.setBorder(new TitledBorder(UIManager.getBorder("TitledBorder.border"),
				Messages.getString("ManualGetUI.panel_2.borderTitle"), TitledBorder.LEFT, TitledBorder.TOP, null,
				new Color(0, 0, 0)));
		panel_2.setLayout(new GridLayout(2, 2, 0, 0));

		chckbxDownloadWithSelected = new JCheckBox(Messages.getString("ManualGetUI.chckbxDownloadWithSelected.text"));
		chckbxDownloadWithSelected
				.setToolTipText(Messages.getString("ManualGetUI.chckbxDownloadWithSelected.toolTipText")); //$NON-NLS-1$
		panel_2.add(chckbxDownloadWithSelected);

		JCheckBox chckbxAddEbookInfo = new JCheckBox(Messages.getString("ManualGetUI.chckbxAddebookinfo.text")); //$NON-NLS-1$
		chckbxAddEbookInfo.setToolTipText(Messages.getString("ManualGetUI.chckbxAddEbookInfo.toolTipText")); //$NON-NLS-1$
		chckbxAddEbookInfo.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				if (txtInput.getText().trim().equals("")) {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("warning.pleaseInputContent"));
					txtInput.requestFocus();
				} else if (chckbxAddEbookInfo.isSelected()) {
					cri = new CopyRightInfo(btnDownload);
					cri.setVisible(true);
				}
				chckbxAddEbookInfo.setSelected(false);
			}
		});
		panel_2.add(chckbxAddEbookInfo);

		JPanel panel_4 = new JPanel();
		panel_4.setBorder(new TitledBorder(UIManager.getBorder("TitledBorder.border"),
				Messages.getString("ManualGetUI.panel_4.borderTitle"), TitledBorder.LEFT, TitledBorder.TOP, null, //$NON-NLS-1$
				new Color(0, 0, 0)));
		panel_3.add(panel_4, "3, 2, fill, top");
		panel_4.setLayout(new GridLayout(2, 2, 0, 0));

		chkboxSplitFile = new JCheckBox(Messages.getString("ManualGetUI.chkboxSplitFile.text")); //$NON-NLS-1$
		chkboxSplitFile.setToolTipText("Cho phép tải số chương trong phạm vi toàn bộ danh sách");
		panel_4.add(chkboxSplitFile);
		chckbxAddEbookInfo.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent arg0) {
				if (arg0.isPopupTrigger()) {
					popupMenu.show(arg0.getComponent(), arg0.getX(), arg0.getY());
				}
			}
		});
		chckbxDownloadWithSelected.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseReleased(MouseEvent e) {
				if (e.isPopupTrigger()) {
					popupMenu.show(e.getComponent(), e.getX(), e.getY());
				}
			}
		});
		panel.add(btnResume, "6, 7, fill, top");
		panel.add(btnHelp, "4, 5, fill, center");
		panel.add(btnCancel, "6, 5, fill, top");
		panel.add(btnDownload, "6, 3, fill, top");
		panel.add(scrollPane_1, "2, 9, 5, 1, fill, fill");

		JLabel lblNewLabel = new JLabel(Messages.getString("ManualGetUI.lblNewLabel.text"));
		panel.add(lblNewLabel, "2, 11");
		panel.add(lblStatus, "4, 11");
		panel.add(progressBar, "2, 13, 5, 1, fill, fill");
		contentPane.setLayout(gl_contentPane);
		enableForm(true);
		getListToCombo("");
	}
}
