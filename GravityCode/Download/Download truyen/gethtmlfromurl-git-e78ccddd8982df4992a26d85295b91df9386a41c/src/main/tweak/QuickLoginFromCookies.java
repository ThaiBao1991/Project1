package main.tweak;

import java.awt.EventQueue;
import java.awt.HeadlessException;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.StringSelection;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.util.ArrayList;
import java.util.Locale;
import java.util.ResourceBundle;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextPane;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.border.EmptyBorder;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonKey;
import common.Enumeration.EnumConfigKey;
import log.CommonLog;
import mk.constant.Constant;
import mkgethtml.Config;
import mkgethtml.SettingOption;
import models.LoginInfo;
import models.PageConfig;
import resource.text.Messages;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.awt.event.ActionEvent;

/**
 * use for quick login if you has cookies on browser(with account already logged
 * in that site)
 * 
 * @author nxcuo
 *
 */
public class QuickLoginFromCookies extends JFrame {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private JPanel contentPane;
	public JComboBox<PageConfig> cboSourceHost;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					QuickLoginFromCookies frame = new QuickLoginFromCookies();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	public QuickLoginFromCookies(PageConfig pageConfig) {
		initlize();
		setSelectionPage(pageConfig);
	}

	public void setSelectionPage(PageConfig pageConfig) {
		int size = cboSourceHost.getItemCount();
		for (int i = 0; i < size; i++) {
			if (cboSourceHost.getItemAt(i).equals(pageConfig)) {
				cboSourceHost.setSelectedIndex(i);
				break;
			}
		}
	}

	/**
	 * Create the frame.
	 */
	public QuickLoginFromCookies() {

		initlize();
	}

	void initlize() {
		try {
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}
		// set UI language
		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		setIconImage(
				Toolkit.getDefaultToolkit().getImage(QuickLoginFromCookies.class.getResource("/resource/box-16.png")));
		setTitle(Messages.getString("QuickLoginFromCookies.this.title")); //$NON-NLS-1$
		setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		setBounds(100, 100, 500, 401);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		setContentPane(contentPane);
		contentPane.setLayout(new FormLayout(new ColumnSpec[] { FormSpecs.RELATED_GAP_COLSPEC,
				FormSpecs.DEFAULT_COLSPEC, FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("max(142dlu;default)"),
				FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"), FormSpecs.RELATED_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("max(77dlu;default)"),
						FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("default:grow"), FormSpecs.RELATED_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
						FormSpecs.RELATED_GAP_ROWSPEC, }));

		JTextPane txtPnlTip = new JTextPane();
		txtPnlTip.setEditable(false);
		txtPnlTip.setBackground(SystemColor.control);
		txtPnlTip.setText(Messages.getString("QuickLoginFromCookies.txtPnlTip.text")); //$NON-NLS-1$
		contentPane.add(txtPnlTip, "2, 2, 5, 1, fill, fill");

		JLabel lblSource = new JLabel(Messages.getString("QuickLoginFromCookies.lblSource.text")); //$NON-NLS-1$
		contentPane.add(lblSource, "2, 4, right, default");

		cboSourceHost = new JComboBox<PageConfig>();
		contentPane.add(cboSourceHost, "4, 4, 3, 1, fill, default");

		JLabel lblCookies = new JLabel(Messages.getString("QuickLoginFromCookies.lblCookies.text")); //$NON-NLS-1$
		contentPane.add(lblCookies, "2, 6");

		JScrollPane scrollPane = new JScrollPane();
		contentPane.add(scrollPane, "4, 6, 3, 1, fill, fill");

		JTextArea txtCookies = new JTextArea();
		scrollPane.setViewportView(txtCookies);

		JButton btnCopyScriptTo = new JButton(Messages.getString("QuickLoginFromCookies.btnCopyScriptTo.text")); //$NON-NLS-1$
		btnCopyScriptTo.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				// copy script to clipboard
				try {
					Clipboard c = Toolkit.getDefaultToolkit().getSystemClipboard();
					String script = ResourceBundle.getBundle("common.commandValue")
							.getString(CommonKey.JSCopyCookiesScript);
					c.setContents(new StringSelection(script), null);

					JOptionPane.showMessageDialog(null, Messages.getGlobalString("message.copyScriptToClipboard"));
				} catch (HeadlessException e) {
					CommonLog.logError(e);
					e.printStackTrace();
				}

			}
		});
		contentPane.add(btnCopyScriptTo, "4, 8");

		JButton btnPasteSave = new JButton(Messages.getString("QuickLoginFromCookies.btnPasteSave.text")); //$NON-NLS-1$
		btnPasteSave.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				// paste and save info
				try {
					String loginInfoCookies = Toolkit.getDefaultToolkit().getSystemClipboard()
							.getData(DataFlavor.stringFlavor).toString();
					String[] lstValue = loginInfoCookies.split("@###@");
					if (lstValue.length == 2) {
						String host = lstValue[0];
						PageConfig pageConfig = (PageConfig) cboSourceHost.getSelectedItem();
						PageConfig currentPageConfig = Config.getHostConfigByPageCode(host);
						if (currentPageConfig != null) {

							if (pageConfig.getPageCode().equalsIgnoreCase(host)) {

								LoginInfo loginInfo = new LoginInfo(pageConfig.getPageCode());
								loginInfo.setCookies(lstValue[1]);
								Config.updateLoginInfo(loginInfo, pageConfig.getPageCode());

								JOptionPane.showMessageDialog(null,
										Messages.getGlobalString("message.saveLoginInfoSuccess"));

							} else {
								int option = JOptionPane.showConfirmDialog(null,
										String.format(
												Messages.getGlobalString("message.cookiesNotMatchWithCurrentHost"),
												host, pageConfig.getPageCode(), host),
										Messages.getGlobalString("title.help"), JOptionPane.YES_NO_OPTION);
								if (option == JOptionPane.YES_OPTION) {
									LoginInfo loginInfo = new LoginInfo(currentPageConfig.getPageCode());
									loginInfo.setCookies(lstValue[1]);
									Config.updateLoginInfo(loginInfo, currentPageConfig.getPageCode());

									JOptionPane.showMessageDialog(null,
											Messages.getGlobalString("message.saveLoginInfoSuccess"));
								}
							}
						} else {
							JOptionPane.showMessageDialog(null, String
									.format(Messages.getGlobalString("notify.hostDoesNotSupportTryAddOne"), host));
						}
					} else {
						JOptionPane.showMessageDialog(null,
								Messages.getGlobalString("message.pasteCookiesFromClipboardFailed"),
								Messages.getGlobalString("title.help"), JOptionPane.WARNING_MESSAGE);
					}
				} catch (HeadlessException | UnsupportedFlavorException | IOException e1) {
					JOptionPane.showMessageDialog(null, Messages.getGlobalString("error.common"),
							Messages.getGlobalString("title.help"), JOptionPane.WARNING_MESSAGE);
					CommonLog.logError(e1);
					e1.printStackTrace();
				}
			}
		});
		contentPane.add(btnPasteSave, "6, 8");

		getListToCombo();
	}

	/*
	 * Load pageconfig from file to combo
	 */
	public void getListToCombo() {
		cboSourceHost.removeAllItems();
		ArrayList<PageConfig> list = Config.getAllHostConfig();
		for (PageConfig pageConfig : list) {
			cboSourceHost.addItem(pageConfig);
		}
	}

}
