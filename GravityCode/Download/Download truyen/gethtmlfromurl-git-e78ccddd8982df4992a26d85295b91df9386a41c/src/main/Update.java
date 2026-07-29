package main;

import java.awt.EventQueue;
import java.awt.Font;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.WindowConstants;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonKey;
import mk.constant.Constant;
import resource.text.Messages;
import utils.CheckUpdate;

public class Update {

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			@Override
			public void run() {
				try {
					Update window = new Update();
					window.frmUpdate.setVisible(true);

				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	public JFrame frmUpdate;
	private JScrollPane scrollPane;
	private JButton btnSkip;
	private JButton btnUpdate;
	private JLabel lblStatus;
	private JTextArea txtMessage;
	private CheckUpdate checkUpdate;
	// value when btnDownload or Cancel is click
	public int BTN_CLICK = -1;

	private JButton btnOpenDownloadPage;

	/**
	 * Create the application.
	 */
	public Update() {
		initialize();
	}

	/**
	 * Create the application
	 * 
	 * @param title
	 *            - windows title
	 * @param message
	 *            - message to be showup
	 * @param btnUpdateText
	 *            - text on button update
	 * @param btnSkipText
	 *            - text on button skip
	 * @param btnExitText
	 *            - text on button exit
	 * @param type
	 *            - 0 is update app and 1 is update config
	 */
	public Update(String title, String message, String btnUpdateText, String btnSkipText, CheckUpdate checkUpdate) {
		initialize();
		frmUpdate.setTitle(title);
		txtMessage.setText(message);
		txtMessage.setCaretPosition(0);
		btnUpdate.setText(btnUpdateText);
		btnSkip.setText(btnSkipText);
		this.checkUpdate = checkUpdate;
	}

	/**
	 * Initialize the contents of the frame.
	 */
	private void initialize() {
		frmUpdate = new JFrame();
		frmUpdate.addWindowListener(new WindowAdapter() {
			@Override
			public void windowOpened(WindowEvent arg0) {

				btnOpenDownloadPage.requestFocus();
			}
		});
		frmUpdate.setAlwaysOnTop(true);
		frmUpdate.setTitle(Messages.getString("Update.frmUpdate.title")); //$NON-NLS-1$
		frmUpdate.setIconImage(Toolkit.getDefaultToolkit().getImage(Update.class.getResource("/resource/box-16.png")));
		frmUpdate.setBounds(100, 100, 587, 205);
		frmUpdate.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		frmUpdate.getContentPane()
				.setLayout(new FormLayout(
						new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("330px:grow"),
								FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("100px"),
								FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("100px"),
								FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
						new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("90px:grow"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, FormSpecs.DEFAULT_ROWSPEC,
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("26px"),
								FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, }));

		scrollPane = new JScrollPane();
		frmUpdate.getContentPane().add(scrollPane, "2, 2, 5, 1, fill, fill");

		txtMessage = new JTextArea();
		txtMessage.setEditable(false);
		txtMessage.setFont(new Font("Tahoma", Font.PLAIN, 12));
		scrollPane.setViewportView(txtMessage);

		lblStatus = new JLabel(String.format(Messages.getGlobalString("status"), ""));
		lblStatus.setIcon(new ImageIcon(Update.class.getResource("/resource/Drops-32px.gif")));
		frmUpdate.getContentPane().add(lblStatus, "2, 4, 5, 1, fill, top");

		btnSkip = new JButton(Messages.getString("Update.btnSkip.text")); //$NON-NLS-1$
		btnSkip.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				frmUpdate.setVisible(false);
				frmUpdate.dispose();
				Main.window.jfrmUiGetHtml.setVisible(true);
			}
		});

		btnUpdate = new JButton(Messages.getString("Update.btnUpdate.text"));
		btnUpdate.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent e) {
				BTN_CLICK = JOptionPane.YES_OPTION;
				btnUpdate.setEnabled(false);
				btnSkip.setEnabled(false);
				// update process
				try {
					// open to count download on sourceforce
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.LinkDownloadApp));

					if (!checkUpdate.isAppUpdated) {
						checkUpdate.updateApp(lblStatus);
					} else if (!checkUpdate.isConfigUpdated) {
						checkUpdate.updateConfig(lblStatus);
					}
				} catch (IOException | URISyntaxException e1) {
					e1.printStackTrace();
				}

			}
		});

		btnOpenDownloadPage = new JButton(Messages.getString("Update.btnOpenDownloadPage.text"));
		btnOpenDownloadPage.setToolTipText(Messages.getString("Update.btnOpenDownloadPage.tooltip"));
		btnOpenDownloadPage.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(ActionEvent arg0) {
				try {
					if (!checkUpdate.isAppUpdated) {
						java.awt.Desktop.getDesktop().browse(new URI("https://mily.vn/gfhulastest"));
					} else {
						java.awt.Desktop.getDesktop()
								.browse(new URI("https://sourceforge.net/projects/gethtmlfromurl/files/"
										+ Constant.CONFIG_DATASITE_FILE + "/download"));
					}
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
				System.exit(0);
			}
		});
		frmUpdate.getContentPane().add(btnOpenDownloadPage, "2, 6, right, default");
		frmUpdate.getContentPane().add(btnUpdate, "4, 6, fill, center");
		frmUpdate.getContentPane().add(btnSkip, "6, 6, fill, fill");
	}
}
