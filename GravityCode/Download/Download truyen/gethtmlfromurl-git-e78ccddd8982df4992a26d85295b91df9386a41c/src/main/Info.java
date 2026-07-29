package main;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.EventQueue;
import java.awt.Font;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Locale;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextPane;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;
import javax.swing.border.EmptyBorder;

import com.jgoodies.forms.layout.ColumnSpec;
import com.jgoodies.forms.layout.FormLayout;
import com.jgoodies.forms.layout.FormSpecs;
import com.jgoodies.forms.layout.RowSpec;

import common.CommonKey;
import common.CommonValue;
import common.Enumeration.EnumConfigKey;
import mk.constant.Constant;
import mkgethtml.SettingOption;
import resource.text.Messages;
import utils.GetFileUtil;

public class Info extends JDialog {

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
					Info frame = new Info();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	private final JPanel contentPanel = new JPanel();
	JLabel lblFacebook;

	JTextPane txtInfo;

	/**
	 * Create the dialog.
	 */
	public Info() {
		addWindowListener(new WindowAdapter() {
			@Override
			public void windowOpened(WindowEvent arg0) {
				String netInfo = GetFileUtil
						.getStringContentFromURI(CommonValue.getSourceForceDirectURL(Constant.SOURCEFORCE_README_FILE));
				if (netInfo != "") {
					txtInfo.setText(netInfo);
					txtInfo.setCaretPosition(2000);
				}
			}
		});
		try

		{
			UIManager.setLookAndFeel("com.sun.java.swing.plaf.windows.WindowsLookAndFeel");
			Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		} catch (ClassNotFoundException | InstantiationException | IllegalAccessException
				| UnsupportedLookAndFeelException e2) {
			// TODO Auto-generated catch block
			e2.printStackTrace();
		}

		setTitle("Infomation");
		setIconImage(Toolkit.getDefaultToolkit().getImage(Info.class.getResource("/resource/box-16.png")));
		setBounds(100, 100, 561, 458);
		getContentPane().setLayout(new BorderLayout());
		contentPanel.setBorder(new EmptyBorder(5, 5, 5, 5));
		getContentPane().add(contentPanel, BorderLayout.CENTER);

		JLabel lblSoftwareGettextfromurl = new JLabel(Messages.getGlobalString("app.shortName"));

		JLabel lblWrittenByMkbyme = new JLabel(Messages.getGlobalString("app.writtenBy"));

		JLabel lblVersion = new JLabel(String.format(Messages.getGlobalString("app.version"), CommonValue.APP_VERSION));

		JLabel lblEmailMkbymegmailcom = new JLabel(
				String.format(Messages.getGlobalString("app.email"), "mkbyme@gmail.com"));

		JLabel lblFbFbmemkbyme = new JLabel(Messages.getGlobalString("app.facebook"));

		JScrollPane scrollPane = new JScrollPane();

		lblFacebook = new JLabel(Messages.getGlobalString("app.longName"));
		lblFacebook.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.LinkFanPage));
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (URISyntaxException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}

			@Override
			public void mouseEntered(MouseEvent e) {
				lblFacebook.setForeground(Color.RED);
			}

			@Override
			public void mouseExited(MouseEvent e) {
				lblFacebook.setForeground(Color.BLUE);
			}
		});
		lblFacebook.setToolTipText(Messages.getString("Info.lblFanpage.tooltip"));
		lblFacebook.setFont(new Font("Tahoma", Font.BOLD, 11));
		lblFacebook.setForeground(new Color(0, 0, 255));

		JLabel lblFanpage = new JLabel(Messages.getString("Info.lblFanpage.text")); //$NON-NLS-1$
		contentPanel.setLayout(new FormLayout(
				new ColumnSpec[] { FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("67px"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, ColumnSpec.decode("143px"),
						FormSpecs.RELATED_GAP_COLSPEC, ColumnSpec.decode("default:grow"),
						FormSpecs.LABEL_COMPONENT_GAP_COLSPEC, },
				new RowSpec[] { FormSpecs.LABEL_COMPONENT_GAP_ROWSPEC, RowSpec.decode("14px"),
						FormSpecs.LINE_GAP_ROWSPEC, RowSpec.decode("14px"), FormSpecs.RELATED_GAP_ROWSPEC,
						RowSpec.decode("14px"), FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("14px"),
						FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("14px"), FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("14px"),
						FormSpecs.RELATED_GAP_ROWSPEC, RowSpec.decode("113px:grow"), FormSpecs.RELATED_GAP_ROWSPEC,
						FormSpecs.DEFAULT_ROWSPEC, }));

		JLabel lblQuickLink = new JLabel(Messages.getString("Info.lblQuickLink.text"));
		lblQuickLink.setFont(new Font("Tahoma", Font.BOLD, 11));
		contentPanel.add(lblQuickLink, "6, 2, center, center");

		JLabel lblHowToDownload = new JLabel(Messages.getString("Info.lblHowToDownload.text"));
		lblHowToDownload.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkHowToUse));
				} catch (IOException e) {
					e.printStackTrace();
				} catch (URISyntaxException e) {
					e.printStackTrace();
				}
			}

			@Override
			public void mouseEntered(MouseEvent e) {
				lblHowToDownload.setForeground(Color.RED);
			}

			@Override
			public void mouseExited(MouseEvent e) {
				lblHowToDownload.setForeground(Color.BLUE);
			}
		});
		lblHowToDownload.setToolTipText(Messages.getString("Info.lbl.tooltip")); //$NON-NLS-1$
		lblHowToDownload.setForeground(Color.BLUE);
		lblHowToDownload.setFont(new Font("Tahoma", Font.ITALIC, 11));
		contentPanel.add(lblHowToDownload, "6, 4, center, center");

		JLabel lblCreatePRCEbook = new JLabel(Messages.getString("Info.lblCreatePRCEbook.text"));
		lblCreatePRCEbook.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkHowToCreateEbook));
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (URISyntaxException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}

			@Override
			public void mouseEntered(MouseEvent e) {
				lblCreatePRCEbook.setForeground(Color.RED);
			}

			@Override
			public void mouseExited(MouseEvent e) {
				lblCreatePRCEbook.setForeground(Color.BLUE);
			}
		});
		lblCreatePRCEbook.setToolTipText(Messages.getString("Info.lbl.tooltip")); //$NON-NLS-1$
		lblCreatePRCEbook.setForeground(Color.BLUE);
		lblCreatePRCEbook.setFont(new Font("Tahoma", Font.ITALIC, 11));
		contentPanel.add(lblCreatePRCEbook, "6, 6, center, default");

		JLabel lblHowToConvert = new JLabel(Messages.getString("Info.lblHowToConvert.text"));
		lblHowToConvert.setToolTipText(Messages.getString("Info.lbl.tooltip")); //$NON-NLS-1$
		lblHowToConvert.setForeground(Color.BLUE);
		lblHowToConvert.setFont(new Font("Tahoma", Font.ITALIC, 11));

		lblHowToConvert.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkHowToConvert));
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (URISyntaxException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}

			@Override
			public void mouseEntered(MouseEvent e) {
				lblHowToConvert.setForeground(Color.RED);
			}

			@Override
			public void mouseExited(MouseEvent e) {
				lblHowToConvert.setForeground(Color.BLUE);
			}
		});
		contentPanel.add(lblHowToConvert, "6, 8, center, default");

		JLabel lblHowToUseHostManager = new JLabel(Messages.getString("Info.lblHowToUseHostManager.text"));
		lblHowToUseHostManager.setToolTipText(Messages.getString("Info.lbl.tooltip")); //$NON-NLS-1$
		lblHowToUseHostManager.setForeground(Color.BLUE);
		lblHowToUseHostManager.setFont(new Font("Tahoma", Font.ITALIC, 11));

		lblHowToUseHostManager.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.GuideLinkAddHost));
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (URISyntaxException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}

			@Override
			public void mouseEntered(MouseEvent e) {
				lblHowToUseHostManager.setForeground(Color.RED);
			}

			@Override
			public void mouseExited(MouseEvent e) {
				lblHowToUseHostManager.setForeground(Color.BLUE);
			}
		});
		contentPanel.add(lblHowToUseHostManager, "6, 10, center, center");

		JLabel lblDownloadLink = new JLabel(Messages.getString("Info.lblHomePage.text"));
		contentPanel.add(lblDownloadLink, "2, 12");

		JLabel lblDownload = new JLabel(Messages.getString("Info.lblDownload.text"));
		lblDownload.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent arg0) {
				try {
					java.awt.Desktop.getDesktop().browse(new URI(CommonKey.LinkDownloadApp));
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (URISyntaxException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}

			@Override
			public void mouseEntered(MouseEvent e) {
				lblDownload.setForeground(Color.RED);
			}

			@Override
			public void mouseExited(MouseEvent e) {
				lblDownload.setForeground(Color.BLUE);
			}
		});
		lblDownload.setToolTipText(Messages.getString("Info.lblDownload.tooltip"));
		lblDownload.setForeground(Color.BLUE);
		lblDownload.setFont(new Font("Tahoma", Font.BOLD, 11));
		contentPanel.add(lblDownload, "4, 12, 3, 1, left, center");

		txtInfo = new JTextPane();
		txtInfo.setFont(new Font("Tahoma", Font.PLAIN, 11));
		txtInfo.setEditable(false);
		txtInfo.setText(
				"╔══════════════════════════════════════════════════════════════╗\r\n║                                   WRITTEN BY MKBYME\r\n╚══════════════════════════════════════════════════════════════╝\r\n#           __      __                                    \r\n#   /'\\_/`\\/\\ \\    /\\ \\                                   \r\n#  /\\      \\ \\ \\/'\\\\ \\ \\____  __  __    ___ ___      __   \r\n#  \\ \\ \\__\\ \\ \\ , < \\ \\ '__`\\/\\ \\/\\ \\ /' __` __`\\  /'__`\\ \r\n#   \\ \\ \\_/\\ \\ \\ \\\\`\\\\ \\ \\M\\ \\ \\ \\_\\ \\/\\ \\/\\ \\/\\ \\/\\  __/ \r\n#    \\ \\_\\\\ \\_\\ \\_\\ \\_\\ \\_,__/\\/`____ \\ \\_\\ \\_\\ \\_\\ \\____\\\r\n#     \\/_/ \\/_/\\/_/\\/_/\\/___/  `/___/> \\/_/\\/_/\\/_/\\/____/\r\n#                                 /\\___/                  \r\n#                                 \\/__/                   \r\n#\tPhần mềm tải truyện chữ đa năng.\r\n#\tLink project: https://sourceforge.net/p/gethtmlfromurl/\r\n#\tHỗ trợ lấy truyện từ các trang đọc truyện online thành dạng HTML\r\n#\tDùng làm ebook PRC bằng phần mềm MobiPRC Creator");
		txtInfo.setCaretPosition(0);
		scrollPane.setViewportView(txtInfo);
		contentPanel.add(scrollPane, "2, 16, 5, 1, fill, fill");
		contentPanel.add(lblSoftwareGettextfromurl, "2, 2, 3, 1, left, top");
		contentPanel.add(lblWrittenByMkbyme, "2, 4, 3, 1, left, top");
		contentPanel.add(lblVersion, "2, 6, 3, 1, left, top");
		contentPanel.add(lblEmailMkbymegmailcom, "2, 8, 3, 1, left, top");
		contentPanel.add(lblFbFbmemkbyme, "2, 10, 3, 1, left, top");
		contentPanel.add(lblFanpage, "2, 14, left, top");
		contentPanel.add(lblFacebook, "4, 14, 3, 1, left, top");
		{
			JButton okButton = new JButton(Messages.getGlobalString("btn.ok"));
			contentPanel.add(okButton, "6, 18, right, default");
			okButton.addActionListener(new ActionListener() {
				@Override
				public void actionPerformed(ActionEvent arg0) {
					setVisible(false);
				}
			});
			getRootPane().setDefaultButton(okButton);
		}
		this.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		this.setVisible(true);
	}
}
