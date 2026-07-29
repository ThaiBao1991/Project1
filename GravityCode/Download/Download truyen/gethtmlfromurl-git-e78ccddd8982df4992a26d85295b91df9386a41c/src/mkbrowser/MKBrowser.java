package mkbrowser;

import java.awt.BorderLayout;
import java.awt.EventQueue;
import java.awt.Toolkit;
import java.io.IOException;
import java.util.Locale;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.border.EmptyBorder;

import common.Enumeration.EnumConfigKey;
import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import mk.constant.Constant;
import mkgethtml.SettingOption;

public class MKBrowser extends JFrame {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private JPanel contentPane;
	private final JFXPanel jfxPanel = new JFXPanel();
	private MiniBrowserController controller = null;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					MKBrowser frame = new MKBrowser();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	/**
	 * Create the frame.
	 */
	public MKBrowser() {
		setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		initComponent();
	}

	private void initComponent() {

		Locale.setDefault(new Locale(SettingOption.getString(EnumConfigKey.LANGUAGE, Constant.DEFAULT_LANGUAGE)));
		createScene();

		setIconImage(Toolkit.getDefaultToolkit().getImage(MKBrowser.class.getResource("/resource/box-16.png")));
		setBounds(100, 100, 850, 470);
		contentPane = new JPanel();
		contentPane.setBorder(new EmptyBorder(5, 5, 5, 5));
		setContentPane(contentPane);
		contentPane.setLayout(new BorderLayout(0, 0));

		contentPane.add(jfxPanel, BorderLayout.CENTER);
	}

	private void createScene() {

		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				try {
					// save controller data
					FXMLLoader loader = new FXMLLoader(getClass().getResource("fxml/mkbrowser.fxml"));
					Parent root = loader.load();
					Scene scene = new Scene(root, 700, 400);
					scene.setUserData(loader);

					jfxPanel.setScene(scene);
				} catch (IOException e) {

					e.printStackTrace();
				}
			}
		});
	}

	/*
	 * load url
	 */
	public void loadURL(final String url) {

		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				jfxPanel.requestFocus();
				if (controller == null) {
					FXMLLoader loader = (FXMLLoader) jfxPanel.getScene().getUserData();
					if (loader != null) {
						controller = loader.getController();
					}
				}
				if (controller != null) {

					controller.loadAddressOnFirst(url);
				}
			}
		});

	}
	/*
	 * load url
	 */
	public void loadURL(final String url,final String pageCode) {

		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				jfxPanel.requestFocus();
				if (controller == null) {
					FXMLLoader loader = (FXMLLoader) jfxPanel.getScene().getUserData();
					if (loader != null) {
						controller = loader.getController();
					}
				}
				if (controller != null) {

					controller.loadAddressOnFirst(url);
					controller.pageCode = pageCode;
				}
			}
		});

	}


}
