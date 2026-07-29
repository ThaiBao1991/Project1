package mk.function;

/**
 * inject funtion and return Object
 * @author nxcuo
 *
 */
public interface FuncParamObject {
	/**
	 * do something with param pass
	 * @param object
	 * @return
	 */
	Object call(Object... object);
}
