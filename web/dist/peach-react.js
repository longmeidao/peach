import { LOC as e, fmtDur as t, fmtSize as n, requestErrorMessage as r } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as i, confirmModal as a, setCollapseOpen as o } from "/js/ui-components.js";
//#region \0rolldown/runtime.js
var s = Object.create, c = Object.defineProperty, l = Object.getOwnPropertyDescriptor, u = Object.getOwnPropertyNames, d = Object.getPrototypeOf, f = Object.prototype.hasOwnProperty, p = (e, t) => () => (t || (e((t = { exports: {} }).exports, t), e = null), t.exports), m = (e, t, n, r) => {
	if (t && typeof t == "object" || typeof t == "function") for (var i = u(t), a = 0, o = i.length, s; a < o; a++) s = i[a], !f.call(e, s) && s !== n && c(e, s, {
		get: ((e) => t[e]).bind(null, s),
		enumerable: !(r = l(t, s)) || r.enumerable
	});
	return e;
}, h = (e, t, n) => (n = e == null ? {} : s(d(e)), m(t || !e || !e.__esModule || !f.call(e, "default") ? c(n, "default", {
	value: e,
	enumerable: !0
}) : n, e)), g = /* @__PURE__ */ p(((e) => {
	var t = Symbol.for("react.transitional.element"), n = Symbol.for("react.portal"), r = Symbol.for("react.fragment"), i = Symbol.for("react.strict_mode"), a = Symbol.for("react.profiler"), o = Symbol.for("react.consumer"), s = Symbol.for("react.context"), c = Symbol.for("react.forward_ref"), l = Symbol.for("react.suspense"), u = Symbol.for("react.memo"), d = Symbol.for("react.lazy"), f = Symbol.for("react.activity"), p = Symbol.for("react.view_transition"), m = Symbol.iterator;
	function h(e) {
		return typeof e != "object" || !e ? null : (e = m && e[m] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var g = {
		isMounted: function() {
			return !1;
		},
		enqueueForceUpdate: function() {},
		enqueueReplaceState: function() {},
		enqueueSetState: function() {}
	}, _ = Object.assign, v = {};
	function y(e, t, n) {
		this.props = e, this.context = t, this.refs = v, this.updater = n || g;
	}
	y.prototype.isReactComponent = {}, y.prototype.setState = function(e, t) {
		if (typeof e != "object" && typeof e != "function" && e != null) throw Error("takes an object of state variables to update or a function which returns an object of state variables.");
		this.updater.enqueueSetState(this, e, t, "setState");
	}, y.prototype.forceUpdate = function(e) {
		this.updater.enqueueForceUpdate(this, e, "forceUpdate");
	};
	function b() {}
	b.prototype = y.prototype;
	function x(e, t, n) {
		this.props = e, this.context = t, this.refs = v, this.updater = n || g;
	}
	var S = x.prototype = new b();
	S.constructor = x, _(S, y.prototype), S.isPureReactComponent = !0;
	var C = Array.isArray;
	function w() {}
	var T = {
		H: null,
		A: null,
		T: null,
		S: null
	}, E = Object.prototype.hasOwnProperty;
	function D(e, n, r) {
		var i = r.ref;
		return {
			$$typeof: t,
			type: e,
			key: n,
			ref: i === void 0 ? null : i,
			props: r
		};
	}
	function O(e, t) {
		return D(e.type, t, e.props);
	}
	function k(e) {
		return typeof e == "object" && !!e && e.$$typeof === t;
	}
	function A(e) {
		var t = {
			"=": "=0",
			":": "=2"
		};
		return "$" + e.replace(/[=:]/g, function(e) {
			return t[e];
		});
	}
	var j = /\/+/g;
	function M(e, t) {
		return typeof e == "object" && e && e.key != null ? A("" + e.key) : t.toString(36);
	}
	function N(e) {
		switch (e.status) {
			case "fulfilled": return e.value;
			case "rejected": throw e.reason;
			default: switch (typeof e.status == "string" ? e.then(w, w) : (e.status = "pending", e.then(function(t) {
				e.status === "pending" && (e.status = "fulfilled", e.value = t);
			}, function(t) {
				e.status === "pending" && (e.status = "rejected", e.reason = t);
			})), e.status) {
				case "fulfilled": return e.value;
				case "rejected": throw e.reason;
			}
		}
		throw e;
	}
	function ee(e, r, i, a, o) {
		var s = typeof e;
		(s === "undefined" || s === "boolean") && (e = null);
		var c = !1;
		if (e === null) c = !0;
		else switch (s) {
			case "bigint":
			case "string":
			case "number":
				c = !0;
				break;
			case "object": switch (e.$$typeof) {
				case t:
				case n:
					c = !0;
					break;
				case d: return c = e._init, ee(c(e._payload), r, i, a, o);
			}
		}
		if (c) return o = o(e), c = a === "" ? "." + M(e, 0) : a, C(o) ? (i = "", c != null && (i = c.replace(j, "$&/") + "/"), ee(o, r, i, "", function(e) {
			return e;
		})) : o != null && (k(o) && (o = O(o, i + (o.key == null || e && e.key === o.key ? "" : ("" + o.key).replace(j, "$&/") + "/") + c)), r.push(o)), 1;
		c = 0;
		var l = a === "" ? "." : a + ":";
		if (C(e)) for (var u = 0; u < e.length; u++) a = e[u], s = l + M(a, u), c += ee(a, r, i, s, o);
		else if (u = h(e), typeof u == "function") for (e = u.call(e), u = 0; !(a = e.next()).done;) a = a.value, s = l + M(a, u++), c += ee(a, r, i, s, o);
		else if (s === "object") {
			if (typeof e.then == "function") return ee(N(e), r, i, a, o);
			throw r = String(e), Error("Objects are not valid as a React child (found: " + (r === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : r) + "). If you meant to render a collection of children, use an array instead.");
		}
		return c;
	}
	function te(e, t, n) {
		if (e == null) return e;
		var r = [], i = 0;
		return ee(e, r, "", "", function(e) {
			return t.call(n, e, i++);
		}), r;
	}
	function P(e) {
		if (e._status === -1) {
			var t = e._result, n = t();
			n.then(function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 1, e._result = t, n.status === void 0 && (n.status = "fulfilled", n.value = t));
			}, function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 2, e._result = t, n.status === void 0 && (n.status = "rejected", n.reason = t));
			}), e._status === -1 && (e._status = 0, e._result = n);
		}
		if (e._status === 1) return e._result.default;
		throw e._result;
	}
	var ne = typeof reportError == "function" ? reportError : function(e) {
		if (typeof window == "object" && typeof window.ErrorEvent == "function") {
			var t = new window.ErrorEvent("error", {
				bubbles: !0,
				cancelable: !0,
				message: typeof e == "object" && e && typeof e.message == "string" ? String(e.message) : String(e),
				error: e
			});
			if (!window.dispatchEvent(t)) return;
		} else if (typeof process == "object" && typeof process.emit == "function") {
			process.emit("uncaughtException", e);
			return;
		}
		console.error(e);
	};
	function F(e) {
		var t = T.T, n = {};
		n.types = t === null ? null : t.types, T.T = n;
		try {
			var r = e(), i = T.S;
			i !== null && i(n, r), typeof r == "object" && r && typeof r.then == "function" && r.then(w, ne);
		} catch (e) {
			ne(e);
		} finally {
			t !== null && n.types !== null && (t.types = n.types), T.T = t;
		}
	}
	function re(e) {
		var t = T.T;
		if (t !== null) {
			var n = t.types;
			n === null ? t.types = [e] : n.indexOf(e) === -1 && n.push(e);
		} else F(re.bind(null, e));
	}
	var ie = {
		map: te,
		forEach: function(e, t, n) {
			te(e, function() {
				t.apply(this, arguments);
			}, n);
		},
		count: function(e) {
			var t = 0;
			return te(e, function() {
				t++;
			}), t;
		},
		toArray: function(e) {
			return te(e, function(e) {
				return e;
			}) || [];
		},
		only: function(e) {
			if (!k(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	};
	e.Activity = f, e.Children = ie, e.Component = y, e.Fragment = r, e.Profiler = a, e.PureComponent = x, e.StrictMode = i, e.Suspense = l, e.ViewTransition = p, e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = T, e.__COMPILER_RUNTIME = {
		__proto__: null,
		c: function(e) {
			return T.H.useMemoCache(e);
		}
	}, e.addTransitionType = re, e.cache = function(e) {
		return function() {
			return e.apply(null, arguments);
		};
	}, e.cacheSignal = function() {
		return null;
	}, e.cloneElement = function(e, t, n) {
		if (e == null) throw Error("The argument must be a React element, but you passed " + e + ".");
		var r = _({}, e.props), i = e.key;
		if (t != null) for (a in t.key !== void 0 && (i = "" + t.key), t) !E.call(t, a) || a === "key" || a === "__self" || a === "__source" || a === "ref" && t.ref === void 0 || (r[a] = t[a]);
		var a = arguments.length - 2;
		if (a === 1) r.children = n;
		else if (1 < a) {
			for (var o = Array(a), s = 0; s < a; s++) o[s] = arguments[s + 2];
			r.children = o;
		}
		return D(e.type, i, r);
	}, e.createContext = function(e) {
		return e = {
			$$typeof: s,
			_currentValue: e,
			_currentValue2: e,
			_threadCount: 0,
			Provider: null,
			Consumer: null
		}, e.Provider = e, e.Consumer = {
			$$typeof: o,
			_context: e
		}, e;
	}, e.createElement = function(e, t, n) {
		var r, i = {}, a = null;
		if (t != null) for (r in t.key !== void 0 && (a = "" + t.key), t) E.call(t, r) && r !== "key" && r !== "__self" && r !== "__source" && (i[r] = t[r]);
		var o = arguments.length - 2;
		if (o === 1) i.children = n;
		else if (1 < o) {
			for (var s = Array(o), c = 0; c < o; c++) s[c] = arguments[c + 2];
			i.children = s;
		}
		if (e && e.defaultProps) for (r in o = e.defaultProps, o) i[r] === void 0 && (i[r] = o[r]);
		return D(e, a, i);
	}, e.createRef = function() {
		return { current: null };
	}, e.forwardRef = function(e) {
		return {
			$$typeof: c,
			render: e
		};
	}, e.isValidElement = k, e.lazy = function(e) {
		return {
			$$typeof: d,
			_payload: {
				_status: -1,
				_result: e
			},
			_init: P
		};
	}, e.memo = function(e, t) {
		return {
			$$typeof: u,
			type: e,
			compare: t === void 0 ? null : t
		};
	}, e.startTransition = F, e.unstable_useCacheRefresh = function() {
		return T.H.useCacheRefresh();
	}, e.use = function(e) {
		return T.H.use(e);
	}, e.useActionState = function(e, t, n) {
		return T.H.useActionState(e, t, n);
	}, e.useCallback = function(e, t) {
		return T.H.useCallback(e, t);
	}, e.useContext = function(e) {
		return T.H.useContext(e);
	}, e.useDebugValue = function() {}, e.useDeferredValue = function(e, t) {
		return T.H.useDeferredValue(e, t);
	}, e.useEffect = function(e, t) {
		return T.H.useEffect(e, t);
	}, e.useEffectEvent = function(e) {
		return T.H.useEffectEvent(e);
	}, e.useId = function() {
		return T.H.useId();
	}, e.useImperativeHandle = function(e, t, n) {
		return T.H.useImperativeHandle(e, t, n);
	}, e.useInsertionEffect = function(e, t) {
		return T.H.useInsertionEffect(e, t);
	}, e.useLayoutEffect = function(e, t) {
		return T.H.useLayoutEffect(e, t);
	}, e.useMemo = function(e, t) {
		return T.H.useMemo(e, t);
	}, e.useOptimistic = function(e, t) {
		return T.H.useOptimistic(e, t);
	}, e.useReducer = function(e, t, n) {
		return T.H.useReducer(e, t, n);
	}, e.useRef = function(e) {
		return T.H.useRef(e);
	}, e.useState = function(e) {
		return T.H.useState(e);
	}, e.useSyncExternalStore = function(e, t, n) {
		return T.H.useSyncExternalStore(e, t, n);
	}, e.useTransition = function() {
		return T.H.useTransition();
	}, e.version = "19.3.0";
})), _ = /* @__PURE__ */ p(((e, t) => {
	t.exports = g();
})), v = /* @__PURE__ */ p(((e) => {
	var t = Symbol.for("react.transitional.element"), n = Symbol.for("react.fragment");
	function r(e, n, r) {
		var i = null;
		if (r !== void 0 && (i = "" + r), n.key !== void 0 && (i = "" + n.key), "key" in n) for (var a in r = {}, n) a !== "key" && (r[a] = n[a]);
		else r = n;
		return n = r.ref, {
			$$typeof: t,
			type: e,
			key: i,
			ref: n === void 0 ? null : n,
			props: r
		};
	}
	e.Fragment = n, e.jsx = r, e.jsxs = r;
})), y = /* @__PURE__ */ p(((e, t) => {
	t.exports = v();
})), b = /* @__PURE__ */ h(_(), 1), x = y(), S = b.createContext(void 0), C = (e) => {
	let t = b.useContext(S);
	if (e) return e;
	if (!t) throw Error("No QueryClient set, use QueryClientProvider to set one");
	return t;
}, w = ({ client: e, children: t }) => (b.useEffect(() => (e.mount(), () => {
	e.unmount();
}), [e]), /* @__PURE__ */ (0, x.jsx)(S.Provider, {
	value: e,
	children: t
})), T = {
	setTimeout: (e, t) => setTimeout(e, t),
	clearTimeout: (e) => clearTimeout(e),
	setInterval: (e, t) => setInterval(e, t),
	clearInterval: (e) => clearInterval(e)
}, E = new class {
	#e = T;
	setTimeoutProvider(e) {
		this.#e = e;
	}
	setTimeout(e, t) {
		return this.#e.setTimeout(e, t);
	}
	clearTimeout(e) {
		this.#e.clearTimeout(e);
	}
	setInterval(e, t) {
		return this.#e.setInterval(e, t);
	}
	clearInterval(e) {
		this.#e.clearInterval(e);
	}
}();
function D(e) {
	setTimeout(e, 0);
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/utils.js
var O = typeof window > "u" || "Deno" in globalThis;
function k() {}
function A(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function j(e) {
	return typeof e == "number" && e >= 0 && e !== Infinity;
}
function M(e, t) {
	return Math.max(e + (t || 0) - Date.now(), 0);
}
function N(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function ee(e, t) {
	let { type: n = "all", exact: r, fetchStatus: i, predicate: a, queryKey: o, stale: s } = e;
	if (o) {
		if (r) {
			if (t.queryHash !== P(o, t.options)) return !1;
		} else if (!F(t.queryKey, o)) return !1;
	}
	if (n !== "all") {
		let e = t.isActive();
		if (n === "active" && !e || n === "inactive" && e) return !1;
	}
	return !(typeof s == "boolean" && t.isStale() !== s || i && i !== t.state.fetchStatus || a && !a(t));
}
function te(e, t) {
	let { exact: n, status: r, predicate: i, mutationKey: a } = e;
	if (a) {
		if (!t.options.mutationKey) return !1;
		if (n) {
			if (ne(t.options.mutationKey) !== ne(a)) return !1;
		} else if (!F(t.options.mutationKey, a)) return !1;
	}
	return !(r && t.state.status !== r || i && !i(t));
}
function P(e, t) {
	return (t?.queryKeyHashFn || ne)(e);
}
function ne(e) {
	return JSON.stringify(e, (e, t) => se(t) ? Object.keys(t).sort().reduce((e, n) => (e[n] = t[n], e), {}) : t);
}
function F(e, t) {
	if (e === t) return !0;
	if (typeof e != typeof t) return !1;
	if (e && t && typeof e == "object" && typeof t == "object") {
		if (Array.isArray(e) && Array.isArray(t)) {
			for (let n = 0; n < t.length; n++) if (!F(e[n], t[n])) return !1;
			return !0;
		}
		let n = Object.keys(t);
		for (let r of n) if (!F(e[r], t[r])) return !1;
		return !0;
	}
	return !1;
}
var re = Object.prototype.hasOwnProperty;
function ie(e, t, n = 0) {
	if (e === t) return e;
	if (n > 500) return t;
	let r = oe(e) && oe(t);
	if (!r && !(se(e) && se(t))) return t;
	let i = (r ? e : Object.keys(e)).length, a = r ? t : Object.keys(t), o = a.length, s = r ? Array(o) : {}, c = 0;
	for (let l = 0; l < o; l++) {
		let o = r ? l : a[l], u = e[o], d = t[o];
		if (u === d) {
			s[o] = u, (r ? l < i : re.call(e, o)) && c++;
			continue;
		}
		if (u === null || d === null || typeof u != "object" || typeof d != "object") {
			s[o] = d;
			continue;
		}
		let f = ie(u, d, n + 1);
		s[o] = f, f === u && c++;
	}
	return i === o && c === i ? e : s;
}
function ae(e, t) {
	if (!t || Object.keys(e).length !== Object.keys(t).length) return !1;
	for (let n in e) if (e[n] !== t[n]) return !1;
	return !0;
}
function oe(e) {
	return Array.isArray(e) && e.length === Object.keys(e).length;
}
function se(e) {
	if (!ce(e)) return !1;
	let t = e.constructor;
	if (t === void 0) return !0;
	let n = t.prototype;
	return !(!ce(n) || !n.hasOwnProperty("isPrototypeOf") || Object.getPrototypeOf(e) !== Object.prototype);
}
function ce(e) {
	return Object.prototype.toString.call(e) === "[object Object]";
}
function le(e) {
	return new Promise((t) => {
		E.setTimeout(t, e);
	});
}
function ue(e, t, n) {
	return typeof n.structuralSharing == "function" ? n.structuralSharing(e, t) : n.structuralSharing === !1 ? t : ie(e, t);
}
function de(e, t, n = 0) {
	let r = [...e, t];
	return n && r.length > n ? r.slice(1) : r;
}
function fe(e, t, n = 0) {
	let r = [t, ...e];
	return n && r.length > n ? r.slice(0, -1) : r;
}
var I = Symbol();
function L(e, t) {
	return !e.queryFn && t?.initialPromise ? () => t.initialPromise : !e.queryFn || e.queryFn === I ? () => Promise.reject(/* @__PURE__ */ Error(`Missing queryFn: '${e.queryHash}'`)) : e.queryFn;
}
function pe(e, t) {
	return typeof e == "function" ? e(...t) : !!e;
}
function me(e, t, n) {
	let r = !1, i;
	return Object.defineProperty(e, "signal", {
		enumerable: !0,
		get: () => (i ??= t(), r ? i : (r = !0, i.aborted ? n() : i.addEventListener("abort", n, { once: !0 }), i))
	}), e;
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/environmentManager.js
var he = () => O, ge = () => he(), _e = class {
	constructor() {
		this.listeners = /* @__PURE__ */ new Set(), this.subscribe = this.subscribe.bind(this);
	}
	subscribe(e) {
		return this.listeners.add(e), this.onSubscribe(), () => {
			this.listeners.delete(e), this.onUnsubscribe();
		};
	}
	hasListeners() {
		return this.listeners.size > 0;
	}
	onSubscribe() {}
	onUnsubscribe() {}
}, ve = new class extends _e {
	#e;
	#t;
	#n;
	constructor() {
		super(), this.#n = (e) => {
			if (typeof window < "u" && window.addEventListener) {
				let t = () => e();
				return window.addEventListener("visibilitychange", t, !1), () => {
					window.removeEventListener("visibilitychange", t);
				};
			}
		};
	}
	onSubscribe() {
		this.#t || this.setEventListener(this.#n);
	}
	onUnsubscribe() {
		this.hasListeners() || (this.#t?.(), this.#t = void 0);
	}
	setEventListener(e) {
		this.#n = e, this.#t?.(), this.#t = e((e) => {
			typeof e == "boolean" ? this.setFocused(e) : this.onFocus();
		});
	}
	setFocused(e) {
		this.#e !== e && (this.#e = e, this.onFocus());
	}
	onFocus() {
		let e = this.isFocused();
		this.listeners.forEach((t) => {
			t(e);
		});
	}
	isFocused() {
		return typeof this.#e == "boolean" ? this.#e : globalThis.document?.visibilityState !== "hidden";
	}
}(), ye = D;
function be() {
	let e = [], t = 0, n = (e) => {
		e();
	}, r = (e) => {
		e();
	}, i = ye, a = (r) => {
		t ? e.push(r) : i(() => {
			n(r);
		});
	}, o = () => {
		let t = e;
		e = [], t.length && i(() => {
			r(() => {
				t.forEach((e) => {
					n(e);
				});
			});
		});
	};
	return {
		batch: (e) => {
			let n;
			t++;
			try {
				n = e();
			} finally {
				t--, t || o();
			}
			return n;
		},
		batchCalls: (e) => (...t) => {
			a(() => {
				e(...t);
			});
		},
		schedule: a,
		setNotifyFunction: (e) => {
			n = e;
		},
		setBatchNotifyFunction: (e) => {
			r = e;
		},
		setScheduler: (e) => {
			i = e;
		}
	};
}
var xe = be(), Se = new class extends _e {
	#e = !0;
	#t;
	#n;
	constructor() {
		super(), this.#n = (e) => {
			if (typeof window < "u" && window.addEventListener) {
				let t = () => e(!0), n = () => e(!1);
				return window.addEventListener("online", t, !1), window.addEventListener("offline", n, !1), () => {
					window.removeEventListener("online", t), window.removeEventListener("offline", n);
				};
			}
		};
	}
	onSubscribe() {
		this.#t || this.setEventListener(this.#n);
	}
	onUnsubscribe() {
		this.hasListeners() || (this.#t?.(), this.#t = void 0);
	}
	setEventListener(e) {
		this.#n = e, this.#t?.(), this.#t = e(this.setOnline.bind(this));
	}
	setOnline(e) {
		this.#e !== e && (this.#e = e, this.listeners.forEach((t) => {
			t(e);
		}));
	}
	isOnline() {
		return this.#e;
	}
}();
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/retryer.js
function Ce(e) {
	return Math.min(1e3 * 2 ** e, 3e4);
}
function we(e) {
	return (e ?? "online") !== "online" || Se.isOnline();
}
var Te = class extends Error {
	constructor(e) {
		super("CancelledError"), this.revert = e?.revert, this.silent = e?.silent;
	}
};
function Ee(e) {
	let t = !1, n = 0, r, i = "pending", a, o, s = new Promise((e, t) => {
		a = e, o = t;
	});
	s.catch(k);
	let c = () => i !== "pending", l = (t) => {
		if (!c()) {
			let n = new Te(t);
			h(n), e.onCancel?.(n);
		}
	}, u = () => {
		t = !0;
	}, d = () => {
		t = !1;
	}, f = () => ve.isFocused() && (e.networkMode === "always" || Se.isOnline()) && e.canRun(), p = () => we(e.networkMode) && e.canRun(), m = (e) => {
		c() || (r?.(), i = "resolved", a(e));
	}, h = (e) => {
		c() || (r?.(), i = "rejected", o(e));
	}, g = () => new Promise((t) => {
		r = (e) => {
			(c() || f()) && t(e);
		}, e.onPause?.();
	}).then(() => {
		r = void 0, c() || e.onContinue?.();
	}), _ = () => {
		if (c()) return;
		let r, i = n === 0 ? e.initialPromise : void 0;
		try {
			r = i ?? e.fn();
		} catch (e) {
			r = Promise.reject(e);
		}
		Promise.resolve(r).then(m).catch((r) => {
			if (c()) return;
			let i = e.retry ?? (ge() ? 0 : 3), a = e.retryDelay ?? Ce, o = typeof a == "function" ? a(n, r) : a, s = i === !0 || typeof i == "number" && n < i || typeof i == "function" && i(n, r);
			if (t || !s) {
				h(r);
				return;
			}
			n++, e.onFail?.(n, r), le(o).then(() => f() ? void 0 : g()).then(() => {
				t ? h(r) : _();
			});
		});
	};
	return {
		promise: s,
		status: () => i,
		cancel: l,
		continue: () => (r?.(), s),
		cancelRetry: u,
		continueRetry: d,
		canStart: p,
		start: () => (p() ? _() : g().then(_), s)
	};
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/removable.js
var De = class {
	#e;
	destroy() {
		this.clearGcTimeout();
	}
	scheduleGc() {
		this.clearGcTimeout(), j(this.gcTime) && (this.#e = E.setTimeout(() => {
			this.optionalRemove();
		}, this.gcTime));
	}
	updateGcTime(e) {
		this.gcTime = Math.max(this.gcTime || 0, e ?? (ge() ? Infinity : 3e5));
	}
	clearGcTimeout() {
		this.#e !== void 0 && (E.clearTimeout(this.#e), this.#e = void 0);
	}
};
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/infiniteQueryBehavior.js
function Oe(e) {
	return { onFetch: (t, n) => {
		let r = t.options, i = t.fetchOptions?.meta?.fetchMore?.direction, a = t.state.data?.pages || [], o = t.state.data?.pageParams || [], s = {
			pages: [],
			pageParams: []
		}, c = 0, l = async () => {
			let n = !1, l = (e) => {
				me(e, () => t.signal, () => n = !0);
			}, u = L(t.options, t.fetchOptions), d = async (e, r, i) => {
				if (n) return Promise.reject(t.signal.reason);
				if (r == null && e.pages.length) return Promise.resolve(e);
				let a = (() => {
					let e = {
						client: t.client,
						queryKey: t.queryKey,
						pageParam: r,
						direction: i ? "backward" : "forward",
						meta: t.options.meta
					};
					return l(e), e;
				})(), o = await u(a), { maxPages: s } = t.options, c = i ? fe : de;
				return {
					pages: c(e.pages, o, s),
					pageParams: c(e.pageParams, r, s)
				};
			};
			if (i && a.length) {
				let e = i === "backward", t = e ? Ae : ke, n = {
					pages: a,
					pageParams: o
				};
				s = await d(n, t(r, n), e);
			} else {
				let t = e ?? a.length;
				do {
					let e = c === 0 ? o[0] ?? r.initialPageParam : ke(r, s);
					if (c > 0 && e == null) break;
					s = await d(s, e), c++;
				} while (c < t);
			}
			return s;
		};
		t.fetchFn = t.options.persister ? () => t.options.persister?.(l, {
			client: t.client,
			queryKey: t.queryKey,
			meta: t.options.meta,
			signal: t.signal
		}, n) : l;
	} };
}
function ke(e, { pages: t, pageParams: n }) {
	let r = t.length - 1;
	return t.length > 0 ? e.getNextPageParam(t[r], t, n[r], n) : void 0;
}
function Ae(e, { pages: t, pageParams: n }) {
	return t.length > 0 ? e.getPreviousPageParam?.(t[0], t, n[0], n) : void 0;
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/query.js
var je = class extends De {
	#e;
	#t;
	#n;
	#r;
	#i;
	#a;
	#o;
	#s;
	constructor(e) {
		super(), this.#s = !1, this.#o = e.defaultOptions, this.setOptions(e.options), this.observers = [], this.#i = e.client, this.#r = this.#i.getQueryCache(), this.queryKey = e.queryKey, this.queryHash = e.queryHash, this.#t = Pe(this.options), this.state = e.state ?? this.#t, this.scheduleGc();
	}
	get meta() {
		return this.options.meta;
	}
	get queryType() {
		return this.#e;
	}
	get promise() {
		return this.#a?.promise;
	}
	setOptions(e) {
		if (this.options = {
			...this.#o,
			...e
		}, e?._type && (this.#e = e._type), this.updateGcTime(this.options.gcTime), this.state && this.state.data === void 0) {
			let e = Pe(this.options);
			e.data !== void 0 && (this.setState(Ne(e.data, e.dataUpdatedAt)), this.#t = e);
		}
	}
	optionalRemove() {
		!this.observers.length && this.state.fetchStatus === "idle" && this.#r.remove(this);
	}
	setData(e, t) {
		let n = ue(this.state.data, e, this.options);
		return this.#c({
			data: n,
			type: "success",
			dataUpdatedAt: t?.updatedAt,
			manual: t?.manual
		}), n;
	}
	setState(e) {
		this.#c({
			type: "setState",
			state: e
		});
	}
	cancel(e) {
		let t = this.#a?.promise;
		return this.#a?.cancel(e), t ? t.then(k).catch(k) : Promise.resolve();
	}
	destroy() {
		super.destroy(), this.cancel({ silent: !0 });
	}
	get resetState() {
		return this.#t;
	}
	reset() {
		this.destroy(), this.setState(this.resetState);
	}
	isActive() {
		return this.observers.some((e) => N(e.options.enabled, this) !== !1);
	}
	isDisabled() {
		return this.getObserversCount() > 0 ? !this.isActive() : this.options.queryFn === I || !this.isFetched();
	}
	isFetched() {
		return this.state.dataUpdateCount + this.state.errorUpdateCount > 0;
	}
	isStatic() {
		return this.getObserversCount() > 0 && this.observers.some((e) => N(e.options.staleTime, this) === "static");
	}
	isStale() {
		return this.getObserversCount() > 0 ? this.observers.some((e) => e.getCurrentResult().isStale) : this.state.data === void 0 || this.state.isInvalidated;
	}
	isStaleByTime(e = 0) {
		return this.state.data === void 0 ? !0 : e === "static" ? !1 : this.state.isInvalidated ? !0 : !M(this.state.dataUpdatedAt, e);
	}
	onFocus() {
		this.observers.find((e) => e.shouldFetchOnWindowFocus())?.refetch({ cancelRefetch: !1 }), this.#a?.continue();
	}
	onOnline() {
		this.observers.find((e) => e.shouldFetchOnReconnect())?.refetch({ cancelRefetch: !1 }), this.#a?.continue();
	}
	addObserver(e) {
		this.observers.includes(e) || (this.observers.push(e), this.clearGcTimeout(), this.#r.notify({
			type: "observerAdded",
			query: this,
			observer: e
		}));
	}
	removeObserver(e) {
		let t = this.observers.indexOf(e);
		t !== -1 && (this.observers.splice(t, 1), this.observers.length || (this.#a && (this.#s || this.state.fetchStatus === "paused" && this.state.status === "pending" ? this.#a.cancel({ revert: !0 }) : this.#a.cancelRetry()), this.scheduleGc()), this.#r.notify({
			type: "observerRemoved",
			query: this,
			observer: e
		}));
	}
	getObserversCount() {
		return this.observers.length;
	}
	invalidate() {
		this.state.isInvalidated || this.#c({ type: "invalidate" });
	}
	async fetch(e, t) {
		if (this.state.fetchStatus !== "idle" && this.#a?.status() !== "rejected") {
			if (this.state.data !== void 0 && t?.cancelRefetch) this.cancel({ silent: !0 });
			else if (this.#a) return this.#a.continueRetry(), this.#a.promise;
		}
		if (e && this.setOptions(e), !this.options.queryFn) {
			let e = this.observers.find((e) => e.options.queryFn);
			e && this.setOptions(e.options);
		}
		let n = new AbortController(), r = (e) => {
			Object.defineProperty(e, "signal", {
				enumerable: !0,
				get: () => (this.#s = !0, n.signal)
			});
		}, i = () => {
			let e = L(this.options, t), n = (() => {
				let e = {
					client: this.#i,
					queryKey: this.queryKey,
					meta: this.meta
				};
				return r(e), e;
			})();
			return this.#s = !1, this.options.persister ? this.options.persister(e, n, this) : e(n);
		}, a = (() => {
			let e = {
				fetchOptions: t,
				options: this.options,
				queryKey: this.queryKey,
				client: this.#i,
				state: this.state,
				fetchFn: i
			};
			return r(e), e;
		})();
		(this.#e === "infinite" ? Oe(this.options.pages) : this.options.behavior)?.onFetch(a, this), this.#n = this.state, (this.state.fetchStatus === "idle" || this.state.fetchMeta !== a.fetchOptions?.meta) && this.#c({
			type: "fetch",
			meta: a.fetchOptions?.meta
		});
		let o = this.#a = Ee({
			initialPromise: t?.initialPromise,
			fn: a.fetchFn,
			onCancel: (e) => {
				e instanceof Te && e.revert && this.setState({
					...this.#n,
					fetchStatus: "idle"
				}), n.abort();
			},
			onFail: (e, t) => {
				this.#c({
					type: "failed",
					failureCount: e,
					error: t
				});
			},
			onPause: () => {
				this.#c({ type: "pause" });
			},
			onContinue: () => {
				this.#c({ type: "continue" });
			},
			retry: a.options.retry,
			retryDelay: a.options.retryDelay,
			networkMode: a.options.networkMode,
			canRun: () => !0
		});
		try {
			let e = await o.start();
			if (e === void 0) throw Error(`${this.queryHash} data is undefined`);
			return this.setData(e), this.#r.config.onSuccess?.(e, this), this.#r.config.onSettled?.(e, this.state.error, this), e;
		} catch (e) {
			if (e instanceof Te) {
				if (e.silent) return this.#a.promise;
				if (e.revert) {
					if (this.state.data === void 0) throw e;
					return this.state.data;
				}
			}
			throw this.#c({
				type: "error",
				error: e
			}), this.#r.config.onError?.(e, this), this.#r.config.onSettled?.(this.state.data, e, this), e;
		} finally {
			this.#a === o && (this.#a = void 0), this.scheduleGc();
		}
	}
	#c(e) {
		let t = (t) => {
			switch (e.type) {
				case "failed": return {
					...t,
					fetchFailureCount: e.failureCount,
					fetchFailureReason: e.error
				};
				case "pause": return {
					...t,
					fetchStatus: "paused"
				};
				case "continue": return {
					...t,
					fetchStatus: "fetching"
				};
				case "fetch": return {
					...t,
					...Me(t.data, this.options),
					fetchMeta: e.meta ?? null
				};
				case "success":
					let n = {
						...t,
						...Ne(e.data, e.dataUpdatedAt),
						dataUpdateCount: t.dataUpdateCount + 1,
						...!e.manual && {
							fetchStatus: "idle",
							fetchFailureCount: 0,
							fetchFailureReason: null
						}
					};
					return this.#n = e.manual ? n : void 0, n;
				case "error":
					let r = e.error;
					return {
						...t,
						error: r,
						errorUpdateCount: t.errorUpdateCount + 1,
						errorUpdatedAt: Date.now(),
						fetchFailureCount: t.fetchFailureCount + 1,
						fetchFailureReason: r,
						fetchStatus: "idle",
						status: "error",
						isInvalidated: !0
					};
				case "invalidate": return {
					...t,
					isInvalidated: !0
				};
				case "setState": return {
					...t,
					...e.state
				};
			}
		};
		this.state = t(this.state), xe.batch(() => {
			this.observers.slice().forEach((e) => {
				e.onQueryUpdate();
			}), this.#r.notify({
				query: this,
				type: "updated",
				action: e
			});
		});
	}
};
function Me(e, t) {
	return {
		fetchFailureCount: 0,
		fetchFailureReason: null,
		fetchStatus: we(t.networkMode) ? "fetching" : "paused",
		...e === void 0 && {
			error: null,
			status: "pending"
		}
	};
}
function Ne(e, t) {
	return {
		data: e,
		dataUpdatedAt: t ?? Date.now(),
		error: null,
		isInvalidated: !1,
		status: "success"
	};
}
function Pe(e) {
	let t = typeof e.initialData == "function" ? e.initialData() : e.initialData, n = t !== void 0, r = n ? typeof e.initialDataUpdatedAt == "function" ? e.initialDataUpdatedAt() : e.initialDataUpdatedAt : 0;
	return {
		data: t,
		dataUpdateCount: 0,
		dataUpdatedAt: n ? r ?? Date.now() : 0,
		error: null,
		errorUpdateCount: 0,
		errorUpdatedAt: 0,
		fetchFailureCount: 0,
		fetchFailureReason: null,
		fetchMeta: null,
		isInvalidated: !1,
		status: n ? "success" : "pending",
		fetchStatus: "idle"
	};
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/queryObserver.js
var Fe = class extends _e {
	#e;
	#t = void 0;
	#n = void 0;
	#r = void 0;
	#i;
	#a;
	#o;
	#s;
	#c;
	#l;
	#u;
	#d;
	#f;
	#p = /* @__PURE__ */ new Set();
	constructor(e, t) {
		super(), this.options = t, this.#e = e, this.#o = null, this.bindMethods(), this.setOptions(t);
	}
	bindMethods() {
		this.refetch = this.refetch.bind(this);
	}
	onSubscribe() {
		this.listeners.size === 1 && (this.#t.addObserver(this), Le(this.#t, this.options) ? this.#m() : this.updateResult(), this.#y());
	}
	onUnsubscribe() {
		this.hasListeners() || this.destroy();
	}
	shouldFetchOnReconnect() {
		return Re(this.#t, this.options, this.options.refetchOnReconnect);
	}
	shouldFetchOnWindowFocus() {
		return Re(this.#t, this.options, this.options.refetchOnWindowFocus);
	}
	destroy() {
		this.listeners = /* @__PURE__ */ new Set(), this.#b(), this.#x(), this.#t.removeObserver(this);
	}
	setOptions(e) {
		let t = this.options, n = this.#t;
		if (this.options = this.#e.defaultQueryOptions(e), this.options.enabled !== void 0 && typeof this.options.enabled != "boolean" && typeof this.options.enabled != "function" && typeof N(this.options.enabled, this.#t) != "boolean") throw Error("Expected enabled to be a boolean or a callback that returns a boolean");
		this.#S(), this.#t.setOptions(this.options), t._defaulted && !ae(this.options, t) && this.#e.getQueryCache().notify({
			type: "observerOptionsUpdated",
			query: this.#t,
			observer: this
		});
		let r = this.hasListeners();
		r && ze(this.#t, n, this.options, t) && this.#m(), this.updateResult(), r && (this.#t !== n || N(this.options.enabled, this.#t) !== N(t.enabled, this.#t) || N(this.options.staleTime, this.#t) !== N(t.staleTime, this.#t)) && this.#g();
		let i = this.#_();
		r && (this.#t !== n || N(this.options.enabled, this.#t) !== N(t.enabled, this.#t) || i !== this.#f) && this.#v(i);
	}
	getOptimisticResult(e) {
		let t = this.#e.getQueryCache().build(this.#e, e), n = this.createResult(t, e);
		return ae(this.getCurrentResult(), n) || (this.#r = n, this.#a = this.options, this.#i = this.#t.state), n;
	}
	getCurrentResult() {
		return this.#r;
	}
	trackResult(e, t) {
		return new Proxy(e, { get: (e, n) => (this.trackProp(n), t?.(n), Reflect.get(e, n)) });
	}
	trackProp(e) {
		this.#p.add(e);
	}
	getCurrentQuery() {
		return this.#t;
	}
	refetch({ ...e } = {}) {
		return this.fetch({ ...e });
	}
	fetchOptimistic(e) {
		let t = this.#e.defaultQueryOptions(e), n = this.#e.getQueryCache().build(this.#e, t), r = () => {}, i, a = new Promise((e) => {
			i = e, r = this.#e.getQueryCache().subscribe((i) => {
				i.type === "updated" && i.query.queryHash === n.queryHash && n.state.data !== void 0 && (r(), e(this.createResult(n, t)));
			});
		});
		return Promise.race([n.fetch().then(() => {
			let e = this.createResult(n, t);
			return i?.(e), e;
		}).finally(() => {
			r();
		}), a]);
	}
	fetch(e) {
		return this.#m({
			...e,
			cancelRefetch: e.cancelRefetch ?? !0
		}).then(() => (this.updateResult(), this.#r));
	}
	#m(e) {
		this.#S();
		let t = this.#t.fetch(this.options, e);
		return e?.throwOnError || (t = t.catch(k)), t;
	}
	#h(e) {
		return !ge() && N(this.options.enabled, this.#t) !== !1 && j(e);
	}
	#g() {
		this.#b();
		let e = N(this.options.staleTime, this.#t);
		if (this.#r.isStale || !this.#h(e)) return;
		let t = M(this.#r.dataUpdatedAt, e) + 1;
		this.#u = E.setTimeout(() => {
			this.#r.isStale || this.updateResult();
		}, t);
	}
	#_() {
		return (typeof this.options.refetchInterval == "function" ? this.options.refetchInterval(this.#t) : this.options.refetchInterval) ?? !1;
	}
	#v(e) {
		this.#x(), this.#f = e, !(this.#f === 0 || !this.#h(this.#f)) && (this.#d = E.setInterval(() => {
			(this.options.refetchIntervalInBackground || ve.isFocused()) && this.#m();
		}, this.#f));
	}
	#y() {
		this.#g(), this.#v(this.#_());
	}
	#b() {
		this.#u !== void 0 && (E.clearTimeout(this.#u), this.#u = void 0);
	}
	#x() {
		this.#d !== void 0 && (E.clearInterval(this.#d), this.#d = void 0);
	}
	createResult(e, t) {
		let n = this.#t, r = this.options, i = this.#r, a = this.#i, o = this.#a, s = e === n ? this.#n : e.state, { state: c } = e, l = { ...c }, u = !1, d;
		if (t._optimisticResults) {
			let i = this.hasListeners(), a = !i && Le(e, t), o = i && ze(e, n, t, r);
			(a || o) && (l = {
				...l,
				...Me(c.data, e.options)
			}), t._optimisticResults === "isRestoring" && (l.fetchStatus = "idle");
		}
		let { error: f, errorUpdatedAt: p, status: m } = l;
		d = l.data;
		let h = !1;
		if (t.placeholderData !== void 0 && d === void 0 && m === "pending") {
			let e;
			i?.isPlaceholderData && t.placeholderData === o?.placeholderData ? (e = i.data, h = !0) : e = typeof t.placeholderData == "function" ? t.placeholderData(this.#l?.state.data, this.#l) : t.placeholderData, e !== void 0 && (m = "success", d = ue(i?.data, e, t), u = !0);
		}
		if (t.select && d !== void 0 && !h) {
			if (i && d === a?.data && t.select === this.#s) d = this.#c;
			else try {
				this.#s = t.select, d = t.select(d), d = ue(i?.data, d, t), this.#c = d, this.#o = null;
			} catch (e) {
				this.#o = e;
			}
		} else d === void 0 && (this.#o = null);
		this.#o && (f = this.#o, d = this.#c, p = Date.now(), m = "error", u = !1);
		let g = l.fetchStatus === "fetching", _ = m === "pending", v = m === "error", y = _ && g, b = d !== void 0;
		return {
			status: m,
			fetchStatus: l.fetchStatus,
			isPending: _,
			isSuccess: m === "success",
			isError: v,
			isInitialLoading: y,
			isLoading: y,
			data: d,
			dataUpdatedAt: l.dataUpdatedAt,
			error: f,
			errorUpdatedAt: p,
			failureCount: l.fetchFailureCount,
			failureReason: l.fetchFailureReason,
			errorUpdateCount: l.errorUpdateCount,
			isFetched: e.isFetched(),
			isFetchedAfterMount: l.dataUpdateCount > s.dataUpdateCount || l.errorUpdateCount > s.errorUpdateCount,
			isFetching: g,
			isRefetching: g && !_,
			isLoadingError: v && !b,
			isPaused: l.fetchStatus === "paused",
			isPlaceholderData: u,
			isRefetchError: v && b,
			isStale: Be(e, t),
			refetch: this.refetch,
			isEnabled: N(t.enabled, e) !== !1
		};
	}
	updateResult() {
		let e = this.#r, t = this.createResult(this.#t, this.options);
		if (this.#i = this.#t.state, this.#a = this.options, this.#i.data !== void 0 && (this.#l = this.#t), ae(t, e)) return;
		this.#r = t;
		let n = (() => {
			if (!e) return !0;
			let { notifyOnChangeProps: t } = this.options, n = typeof t == "function" ? t() : t;
			if (n === "all" || !n && !this.#p.size) return !0;
			let r = new Set(n ?? this.#p);
			return this.options.throwOnError && r.add("error"), Object.keys(this.#r).some((t) => {
				let n = t;
				return this.#r[n] !== e[n] && r.has(n);
			});
		})();
		xe.batch(() => {
			n && this.listeners.forEach((e) => {
				e(this.#r);
			}), this.#e.getQueryCache().notify({
				query: this.#t,
				type: "observerResultsUpdated"
			});
		});
	}
	#S() {
		let e = this.#e.getQueryCache().build(this.#e, this.options);
		if (e === this.#t) return;
		let t = this.#t;
		this.#t = e, this.#n = e.state, this.hasListeners() && (t?.removeObserver(this), e.addObserver(this));
	}
	onQueryUpdate() {
		this.updateResult(), this.hasListeners() && this.#y();
	}
};
function Ie(e, t) {
	return N(t.enabled, e) !== !1 && e.state.data === void 0 && (e.state.status !== "error" || N(t.retryOnMount, e) !== !1);
}
function Le(e, t) {
	return Ie(e, t) || e.state.data !== void 0 && Re(e, t, t.refetchOnMount);
}
function Re(e, t, n) {
	if (N(t.enabled, e) !== !1 && N(t.staleTime, e) !== "static") {
		let r = typeof n == "function" ? n(e) : n;
		return r === "always" || r !== !1 && Be(e, t);
	}
	return !1;
}
function ze(e, t, n, r) {
	return (e !== t || N(r.enabled, e) === !1) && (!n.suspense || e.state.status !== "error") && Be(e, n);
}
function Be(e, t) {
	return N(t.enabled, e) !== !1 && e.isStaleByTime(N(t.staleTime, e));
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/mutation.js
var Ve = class extends De {
	#e;
	#t;
	#n;
	#r;
	constructor(e) {
		super(), this.#e = e.client, this.mutationId = e.mutationId, this.#n = e.mutationCache, this.#t = [], this.state = e.state || He(), this.setOptions(e.options), this.scheduleGc();
	}
	setOptions(e) {
		this.options = e, this.updateGcTime(this.options.gcTime);
	}
	get meta() {
		return this.options.meta;
	}
	addObserver(e) {
		this.#t.includes(e) || (this.#t.push(e), this.clearGcTimeout(), this.#n.notify({
			type: "observerAdded",
			mutation: this,
			observer: e
		}));
	}
	removeObserver(e) {
		this.#t = this.#t.filter((t) => t !== e), this.scheduleGc(), this.#n.notify({
			type: "observerRemoved",
			mutation: this,
			observer: e
		});
	}
	optionalRemove() {
		this.#t.length || (this.state.status === "pending" ? this.scheduleGc() : this.#n.remove(this));
	}
	continue() {
		return this.#r?.continue() ?? (this.state.status === "pending" ? this.execute(this.state.variables) : Promise.resolve());
	}
	async execute(e) {
		let t = () => {
			this.#i({ type: "continue" });
		}, n = {
			client: this.#e,
			meta: this.options.meta,
			mutationKey: this.options.mutationKey
		}, r = this.#r = Ee({
			fn: () => this.options.mutationFn ? this.options.mutationFn(e, n) : Promise.reject(/* @__PURE__ */ Error("No mutationFn found")),
			onFail: (e, t) => {
				this.#i({
					type: "failed",
					failureCount: e,
					error: t
				});
			},
			onPause: () => {
				this.#i({ type: "pause" });
			},
			onContinue: t,
			retry: this.options.retry ?? 0,
			retryDelay: this.options.retryDelay,
			networkMode: this.options.networkMode,
			canRun: () => this.#n.canRun(this)
		}), i = this.state.status === "pending", a = !r.canStart();
		try {
			if (i) t();
			else {
				this.#i({
					type: "pending",
					variables: e,
					isPaused: a
				}), this.#n.config.onMutate && await this.#n.config.onMutate(e, this, n);
				let t = await this.options.onMutate?.(e, n);
				t !== this.state.context && this.#i({
					type: "pending",
					context: t,
					variables: e,
					isPaused: a
				});
			}
			let o = await r.start();
			return await this.#n.config.onSuccess?.(o, e, this.state.context, this, n), await this.options.onSuccess?.(o, e, this.state.context, n), await this.#n.config.onSettled?.(o, null, this.state.variables, this.state.context, this, n), await this.options.onSettled?.(o, null, e, this.state.context, n), this.#i({
				type: "success",
				data: o
			}), o;
		} catch (t) {
			try {
				await this.#n.config.onError?.(t, e, this.state.context, this, n);
			} catch (e) {
				Promise.reject(e);
			}
			try {
				await this.options.onError?.(t, e, this.state.context, n);
			} catch (e) {
				Promise.reject(e);
			}
			try {
				await this.#n.config.onSettled?.(void 0, t, this.state.variables, this.state.context, this, n);
			} catch (e) {
				Promise.reject(e);
			}
			try {
				await this.options.onSettled?.(void 0, t, e, this.state.context, n);
			} catch (e) {
				Promise.reject(e);
			}
			throw this.#i({
				type: "error",
				error: t
			}), t;
		} finally {
			this.#r === r && (this.#r = void 0), this.#n.runNext(this);
		}
	}
	#i(e) {
		let t = (t) => {
			switch (e.type) {
				case "failed": return {
					...t,
					failureCount: e.failureCount,
					failureReason: e.error
				};
				case "pause": return {
					...t,
					isPaused: !0
				};
				case "continue": return {
					...t,
					isPaused: !1
				};
				case "pending": return {
					...t,
					context: e.context,
					data: void 0,
					failureCount: 0,
					failureReason: null,
					error: null,
					isPaused: e.isPaused,
					status: "pending",
					variables: e.variables,
					submittedAt: Date.now()
				};
				case "success": return {
					...t,
					data: e.data,
					failureCount: 0,
					failureReason: null,
					error: null,
					status: "success",
					isPaused: !1
				};
				case "error": return {
					...t,
					data: void 0,
					error: e.error,
					failureCount: t.failureCount + 1,
					failureReason: e.error,
					isPaused: !1,
					status: "error"
				};
			}
		};
		this.state = t(this.state), xe.batch(() => {
			this.#t.forEach((t) => {
				t.onMutationUpdate(e);
			}), this.#n.notify({
				mutation: this,
				type: "updated",
				action: e
			});
		});
	}
};
function He() {
	return {
		context: void 0,
		data: void 0,
		error: null,
		failureCount: 0,
		failureReason: null,
		isPaused: !1,
		status: "idle",
		variables: void 0,
		submittedAt: 0
	};
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/mutationCache.js
var Ue = class extends _e {
	#e;
	#t;
	#n;
	constructor(e = {}) {
		super(), this.config = e, this.#e = /* @__PURE__ */ new Set(), this.#t = /* @__PURE__ */ new Map(), this.#n = 0;
	}
	build(e, t, n) {
		let r = new Ve({
			client: e,
			mutationCache: this,
			mutationId: ++this.#n,
			options: e.defaultMutationOptions(t),
			state: n
		});
		return this.add(r), r;
	}
	add(e) {
		this.#e.add(e);
		let t = We(e);
		if (typeof t == "string") {
			let n = this.#t.get(t);
			n ? n.push(e) : this.#t.set(t, [e]);
		}
		this.notify({
			type: "added",
			mutation: e
		});
	}
	remove(e) {
		if (this.#e.delete(e)) {
			let t = We(e);
			if (typeof t == "string") {
				let n = this.#t.get(t);
				if (n) {
					if (n.length > 1) {
						let t = n.indexOf(e);
						t !== -1 && n.splice(t, 1);
					} else n[0] === e && this.#t.delete(t);
				}
			}
		}
		this.notify({
			type: "removed",
			mutation: e
		});
	}
	canRun(e) {
		let t = We(e);
		if (typeof t == "string") {
			let n = this.#t.get(t)?.find((e) => e.state.status === "pending");
			return !n || n === e;
		}
		return !0;
	}
	runNext(e) {
		let t = We(e);
		return typeof t == "string" ? (this.#t.get(t)?.find((t) => t !== e && t.state.isPaused))?.continue() ?? Promise.resolve() : Promise.resolve();
	}
	clear() {
		xe.batch(() => {
			this.#e.forEach((e) => {
				this.notify({
					type: "removed",
					mutation: e
				});
			}), this.#e.clear(), this.#t.clear();
		});
	}
	getAll() {
		return Array.from(this.#e);
	}
	find(e) {
		let t = {
			exact: !0,
			...e
		};
		return this.getAll().find((e) => te(t, e));
	}
	findAll(e = {}) {
		return this.getAll().filter((t) => te(e, t));
	}
	notify(e) {
		xe.batch(() => {
			this.listeners.forEach((t) => {
				t(e);
			});
		});
	}
	resumePausedMutations() {
		let e = this.getAll().filter((e) => e.state.isPaused);
		return xe.batch(() => Promise.all(e.map((e) => e.continue().catch(k))));
	}
};
function We(e) {
	return e.options.scope?.id;
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/queryCache.js
var Ge = class extends _e {
	#e;
	constructor(e = {}) {
		super(), this.config = e, this.#e = /* @__PURE__ */ new Map();
	}
	build(e, t, n) {
		let r = t.queryKey, i = t.queryHash ?? P(r, t), a = this.get(i);
		return a || (a = new je({
			client: e,
			queryKey: r,
			queryHash: i,
			options: e.defaultQueryOptions(t),
			state: n,
			defaultOptions: e.getQueryDefaults(r)
		}), this.add(a)), a;
	}
	add(e) {
		this.#e.has(e.queryHash) || (this.#e.set(e.queryHash, e), this.notify({
			type: "added",
			query: e
		}));
	}
	remove(e) {
		let t = this.#e.get(e.queryHash);
		t && (e.destroy(), t === e && this.#e.delete(e.queryHash), this.notify({
			type: "removed",
			query: e
		}));
	}
	clear() {
		xe.batch(() => {
			this.getAll().forEach((e) => {
				this.remove(e);
			});
		});
	}
	get(e) {
		return this.#e.get(e);
	}
	getAll() {
		return [...this.#e.values()];
	}
	find(e) {
		let t = {
			exact: !0,
			...e
		};
		return this.getAll().find((e) => ee(t, e));
	}
	findAll(e = {}) {
		let t = this.getAll();
		return Object.keys(e).length > 0 ? t.filter((t) => ee(e, t)) : t;
	}
	notify(e) {
		xe.batch(() => {
			this.listeners.forEach((t) => {
				t(e);
			});
		});
	}
	onFocus() {
		xe.batch(() => {
			this.getAll().forEach((e) => {
				e.onFocus();
			});
		});
	}
	onOnline() {
		xe.batch(() => {
			this.getAll().forEach((e) => {
				e.onOnline();
			});
		});
	}
}, Ke = class {
	#e;
	#t;
	#n;
	#r;
	#i;
	#a;
	#o;
	#s;
	constructor(e = {}) {
		this.#e = e.queryCache || new Ge(), this.#t = e.mutationCache || new Ue(), this.#n = e.defaultOptions || {}, this.#r = /* @__PURE__ */ new Map(), this.#i = /* @__PURE__ */ new Map(), this.#a = 0;
	}
	mount() {
		this.#a++, this.#a === 1 && (this.#o = ve.subscribe(async (e) => {
			e && (await this.resumePausedMutations(), this.#e.onFocus());
		}), this.#s = Se.subscribe(async (e) => {
			e && (await this.resumePausedMutations(), this.#e.onOnline());
		}));
	}
	unmount() {
		this.#a--, this.#a === 0 && (this.#o?.(), this.#o = void 0, this.#s?.(), this.#s = void 0);
	}
	isFetching(e) {
		return this.#e.findAll({
			...e,
			fetchStatus: "fetching"
		}).length;
	}
	isMutating(e) {
		return this.#t.findAll({
			...e,
			status: "pending"
		}).length;
	}
	getQueryData(e) {
		let t = this.defaultQueryOptions({ queryKey: e });
		return this.#e.get(t.queryHash)?.state.data;
	}
	ensureQueryData(e) {
		let t = this.defaultQueryOptions(e), n = this.#e.build(this, t), r = n.state.data;
		return r === void 0 ? this.fetchQuery(e) : (e.revalidateIfStale && n.isStaleByTime(N(t.staleTime, n)) && this.prefetchQuery(t), Promise.resolve(r));
	}
	getQueriesData(e) {
		return this.#e.findAll(e).map(({ queryKey: e, state: t }) => [e, t.data]);
	}
	setQueryData(e, t, n) {
		let r = this.defaultQueryOptions({ queryKey: e }), i = this.#e.get(r.queryHash)?.state.data, a = A(t, i);
		if (a !== void 0) return this.#e.build(this, r).setData(a, {
			...n,
			manual: !0
		});
	}
	setQueriesData(e, t, n) {
		return xe.batch(() => this.#e.findAll(e).map(({ queryKey: e }) => [e, this.setQueryData(e, t, n)]));
	}
	getQueryState(e) {
		let t = this.defaultQueryOptions({ queryKey: e });
		return this.#e.get(t.queryHash)?.state;
	}
	removeQueries(e) {
		let t = this.#e;
		xe.batch(() => {
			t.findAll(e).forEach((e) => {
				t.remove(e);
			});
		});
	}
	resetQueries(e, t) {
		let n = this.#e;
		return xe.batch(() => {
			let r = n.findAll(e), i = new Set(r);
			return r.forEach((e) => {
				e.reset();
			}), this.refetchQueries({
				type: "active",
				predicate: (e) => i.has(e)
			}, t);
		});
	}
	cancelQueries(e, t = {}) {
		let n = {
			revert: !0,
			...t
		}, r = xe.batch(() => this.#e.findAll(e).map((e) => e.cancel(n)));
		return Promise.all(r).then(k).catch(k);
	}
	invalidateQueries(e, t = {}) {
		return xe.batch(() => (this.#e.findAll(e).forEach((e) => {
			e.invalidate();
		}), e?.refetchType === "none" ? Promise.resolve() : this.refetchQueries({
			...e,
			type: e?.refetchType ?? e?.type ?? "active"
		}, t)));
	}
	refetchQueries(e, t = {}) {
		let n = {
			...t,
			cancelRefetch: t.cancelRefetch ?? !0
		}, r = xe.batch(() => this.#e.findAll(e).filter((e) => !e.isDisabled() && !e.isStatic()).map((e) => {
			let t = e.fetch(void 0, n);
			return n.throwOnError || (t = t.catch(k)), e.state.fetchStatus === "paused" ? Promise.resolve() : t;
		}));
		return Promise.all(r).then(k);
	}
	async query(e) {
		let t = this.defaultQueryOptions(e);
		t.retry === void 0 && (t.retry = !1);
		let n = this.#e.build(this, t), r = n.isStaleByTime(N(t.staleTime, n)) ? await n.fetch(t) : n.state.data, i = t.select;
		return i ? i(r) : r;
	}
	fetchQuery(e) {
		let t = this.defaultQueryOptions(e);
		t.retry === void 0 && (t.retry = !1);
		let n = this.#e.build(this, t);
		return n.isStaleByTime(N(t.staleTime, n)) ? n.fetch(t) : Promise.resolve(n.state.data);
	}
	prefetchQuery(e) {
		return this.fetchQuery(e).then(k).catch(k);
	}
	infiniteQuery(e) {
		return e._type = "infinite", this.query(e);
	}
	fetchInfiniteQuery(e) {
		return e._type = "infinite", this.fetchQuery(e);
	}
	prefetchInfiniteQuery(e) {
		return this.fetchInfiniteQuery(e).then(k).catch(k);
	}
	ensureInfiniteQueryData(e) {
		return e._type = "infinite", this.ensureQueryData(e);
	}
	resumePausedMutations() {
		return Se.isOnline() ? this.#t.resumePausedMutations() : Promise.resolve();
	}
	getQueryCache() {
		return this.#e;
	}
	getMutationCache() {
		return this.#t;
	}
	getDefaultOptions() {
		return this.#n;
	}
	setDefaultOptions(e) {
		this.#n = e;
	}
	setQueryDefaults(e, t) {
		this.#r.set(ne(e), {
			queryKey: e,
			defaultOptions: t
		});
	}
	getQueryDefaults(e) {
		let t = [...this.#r.values()], n = {};
		return t.forEach((t) => {
			F(e, t.queryKey) && Object.assign(n, t.defaultOptions);
		}), n;
	}
	setMutationDefaults(e, t) {
		this.#i.set(ne(e), {
			mutationKey: e,
			defaultOptions: t
		});
	}
	getMutationDefaults(e) {
		let t = [...this.#i.values()], n = {};
		return t.forEach((t) => {
			F(e, t.mutationKey) && Object.assign(n, t.defaultOptions);
		}), n;
	}
	defaultQueryOptions(e) {
		if (e._defaulted) return e;
		let t = {
			...this.#n.queries,
			...this.getQueryDefaults(e.queryKey),
			...e,
			_defaulted: !0
		};
		return t.queryHash ||= P(t.queryKey, t), t.refetchOnReconnect === void 0 && (t.refetchOnReconnect = t.networkMode !== "always"), t.throwOnError === void 0 && (t.throwOnError = !!t.suspense), !t.networkMode && t.persister && (t.networkMode = "offlineFirst"), t.queryFn === I && (t.enabled = !1), t;
	}
	defaultMutationOptions(e) {
		return e?._defaulted ? e : {
			...this.#n.mutations,
			...e?.mutationKey && this.getMutationDefaults(e.mutationKey),
			...e,
			_defaulted: !0
		};
	}
	clear() {
		this.#e.clear(), this.#t.clear();
	}
}, qe = b.createContext(!1), Je = () => b.useContext(qe);
qe.Provider;
//#endregion
//#region node_modules/@tanstack/react-query/build/modern/QueryErrorResetBoundary.js
function Ye() {
	let e = !1;
	return {
		clearReset: () => {
			e = !1;
		},
		reset: () => {
			e = !0;
		},
		isReset: () => e
	};
}
var Xe = b.createContext(Ye()), Ze = () => b.useContext(Xe), Qe = (e, t, n) => {
	let r = n?.state.error && typeof e.throwOnError == "function" ? pe(e.throwOnError, [n.state.error, n]) : e.throwOnError;
	(e.suspense || r) && (t.isReset() || (e.retryOnMount = !1));
}, $e = (e) => {
	b.useEffect(() => {
		e.clearReset();
	}, [e]);
}, et = ({ result: e, errorResetBoundary: t, throwOnError: n, query: r, suspense: i }) => e.isError && !t.isReset() && !e.isFetching && r && (i && e.data === void 0 || pe(n, [e.error, r])), tt = (e) => {
	if (e.suspense) {
		let t = 1e3, n = (e) => e === "static" ? e : Math.max(e ?? t, t), r = e.staleTime;
		e.staleTime = typeof r == "function" ? (...e) => n(r(...e)) : n(r), typeof e.gcTime == "number" && (e.gcTime = Math.max(e.gcTime, t));
	}
}, nt = (e, t) => e?.suspense && t.isPending, rt = (e, t, n) => t.fetchOptimistic(e).catch(() => {
	n.clearReset();
});
//#endregion
//#region node_modules/@tanstack/react-query/build/modern/useBaseQuery.js
function it(e, t, n) {
	let r = Je(), i = Ze(), a = C(n), o = a.defaultQueryOptions(e), s = a.getQueryCache().get(o.queryHash), c = e.subscribed !== !1;
	o._optimisticResults = r ? "isRestoring" : c ? "optimistic" : void 0, tt(o), Qe(o, i, s), $e(i);
	let [l] = b.useState(() => new t(a, o)), u = l.getOptimisticResult(o), d = !r && c;
	if (b.useSyncExternalStore(b.useCallback((e) => {
		let t = d ? l.subscribe(xe.batchCalls(e)) : k;
		return l.updateResult(), t;
	}, [l, d]), () => l.getCurrentResult(), () => l.getCurrentResult()), b.useEffect(() => {
		l.setOptions(o);
	}, [o, l]), nt(o, u)) throw rt(o, l, i);
	if (et({
		result: u,
		errorResetBoundary: i,
		throwOnError: o.throwOnError,
		query: s,
		suspense: o.suspense
	})) throw u.error;
	return o.notifyOnChangeProps ? u : l.trackResult(u);
}
//#endregion
//#region node_modules/@tanstack/react-query/build/modern/useQuery.js
function at(e, t) {
	return it(e, Fe, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/collections/BaseCollection.mjs
var ot = class {
	constructor(e) {
		this.value = null, this.level = 0, this.hasChildNodes = !1, this.rendered = null, this.textValue = "", this["aria-label"] = void 0, this.index = 0, this.parentKey = null, this.prevKey = null, this.nextKey = null, this.firstChildKey = null, this.lastChildKey = null, this.props = {}, this.colSpan = null, this.colIndex = null, this.type = this.constructor.type, this.key = e;
	}
	get childNodes() {
		throw Error("childNodes is not supported");
	}
	clone() {
		let e = new this.constructor(this.key);
		return e.value = this.value, e.level = this.level, e.hasChildNodes = this.hasChildNodes, e.rendered = this.rendered, e.textValue = this.textValue, e["aria-label"] = this["aria-label"], e.index = this.index, e.parentKey = this.parentKey, e.prevKey = this.prevKey, e.nextKey = this.nextKey, e.firstChildKey = this.firstChildKey, e.lastChildKey = this.lastChildKey, e.props = this.props, e.render = this.render, e.colSpan = this.colSpan, e.colIndex = this.colIndex, e;
	}
	filter(e, t, n) {
		let r = this.clone();
		return t.addDescendants(r, e), r;
	}
}, st = class extends ot {
	filter(e, t, n) {
		let [r, i] = dt(e, t, this.firstChildKey, n), a = this.clone();
		return a.firstChildKey = r, a.lastChildKey = i, a;
	}
};
(class extends ot {
	static {
		this.type = "header";
	}
});
var ct = class extends ot {
	static {
		this.type = "loader";
	}
}, lt = class extends st {
	static {
		this.type = "item";
	}
	filter(e, t, n) {
		if (n(this.textValue, this)) {
			let n = this.clone();
			return t.addDescendants(n, e), n;
		}
		return null;
	}
};
(class extends st {
	static {
		this.type = "section";
	}
	filter(e, t, n) {
		let r = super.filter(e, t, n);
		if (r && r.lastChildKey !== null) {
			let t = e.getItem(r.lastChildKey);
			if (t && t.type !== "header") return r;
		}
		return null;
	}
});
var ut = class {
	get size() {
		return this.itemCount;
	}
	getKeys() {
		return this.keyMap.keys();
	}
	*[Symbol.iterator]() {
		let e = this.firstKey == null ? void 0 : this.keyMap.get(this.firstKey);
		for (; e;) yield e, e = e.nextKey == null ? void 0 : this.keyMap.get(e.nextKey);
	}
	getChildren(e) {
		let t = this.keyMap;
		return { *[Symbol.iterator]() {
			let n = t.get(e), r = n?.firstChildKey == null ? null : t.get(n.firstChildKey);
			for (; r;) yield r, r = r.nextKey == null ? void 0 : t.get(r.nextKey);
		} };
	}
	getKeyBefore(e) {
		let t = this.keyMap.get(e);
		if (!t) return null;
		if (t.prevKey != null) {
			for (t = this.keyMap.get(t.prevKey); t && t.type !== "item" && t.lastChildKey != null;) t = this.keyMap.get(t.lastChildKey);
			return t?.key ?? null;
		}
		return t.parentKey;
	}
	getKeyAfter(e) {
		let t = this.keyMap.get(e);
		if (!t) return null;
		if (t.type !== "item" && t.firstChildKey != null) return t.firstChildKey;
		for (; t;) {
			if (t.nextKey != null) return t.nextKey;
			if (t.parentKey != null) t = this.keyMap.get(t.parentKey);
			else return null;
		}
		return null;
	}
	getFirstKey() {
		return this.firstKey;
	}
	getLastKey() {
		let e = this.lastKey == null ? null : this.keyMap.get(this.lastKey);
		for (; e?.lastChildKey != null;) e = this.keyMap.get(e.lastChildKey);
		return e?.key ?? null;
	}
	getItem(e) {
		return this.keyMap.get(e) ?? null;
	}
	at() {
		throw Error("Not implemented");
	}
	clone() {
		let e = this.constructor, t = new e();
		return t.keyMap = new Map(this.keyMap), t.firstKey = this.firstKey, t.lastKey = this.lastKey, t.itemCount = this.itemCount, t;
	}
	addNode(e) {
		if (this.frozen) throw Error("Cannot add a node to a frozen collection");
		e.type === "item" && this.keyMap.get(e.key) == null && this.itemCount++, this.keyMap.set(e.key, e);
	}
	addDescendants(e, t) {
		this.addNode(e);
		let n = t.getChildren(e.key);
		for (let e of n) this.addDescendants(e, t);
	}
	removeNode(e) {
		if (this.frozen) throw Error("Cannot remove a node to a frozen collection");
		let t = this.keyMap.get(e);
		t != null && t.type === "item" && this.itemCount--, this.keyMap.delete(e);
	}
	commit(e, t, n = !1) {
		if (this.frozen) throw Error("Cannot commit a frozen collection");
		this.firstKey = e, this.lastKey = t, this.frozen = !n;
	}
	filter(e) {
		let t = new this.constructor(), [n, r] = dt(this, t, this.firstKey, e);
		return t?.commit(n, r), t;
	}
	constructor() {
		this.keyMap = /* @__PURE__ */ new Map(), this.firstKey = null, this.lastKey = null, this.frozen = !1, this.itemCount = 0;
	}
};
function dt(e, t, n, r) {
	if (n == null) return [null, null];
	let i = null, a = null, o = e.getItem(n);
	for (; o != null;) {
		let n = o.filter(e, t, r);
		n != null && (n.nextKey = null, a && (n.prevKey = a.key, a.nextKey = n.key), i ??= n, t.addNode(n), a = n), o = o.nextKey == null ? null : e.getItem(o.nextKey);
	}
	if (a && a.type === "separator") {
		let e = a.prevKey;
		t.removeNode(a.key), e == null ? a = null : (a = t.getItem(e), a.nextKey = null);
	}
	return [i?.key ?? null, a?.key ?? null];
}
//#endregion
//#region node_modules/react-aria/dist/private/collections/Document.mjs
var ft = class {
	constructor(e) {
		this._firstChild = null, this._lastChild = null, this._previousSibling = null, this._nextSibling = null, this._parentNode = null, this._minInvalidChildIndex = null, this.ownerDocument = e;
	}
	*[Symbol.iterator]() {
		let e = this.firstChild;
		for (; e;) yield e, e = e.nextSibling;
	}
	get firstChild() {
		return this._firstChild;
	}
	set firstChild(e) {
		this._firstChild = e, this.ownerDocument.markDirty(this);
	}
	get lastChild() {
		return this._lastChild;
	}
	set lastChild(e) {
		this._lastChild = e, this.ownerDocument.markDirty(this);
	}
	get previousSibling() {
		return this._previousSibling;
	}
	set previousSibling(e) {
		this._previousSibling = e, this.ownerDocument.markDirty(this);
	}
	get nextSibling() {
		return this._nextSibling;
	}
	set nextSibling(e) {
		this._nextSibling = e, this.ownerDocument.markDirty(this);
	}
	get parentNode() {
		return this._parentNode;
	}
	set parentNode(e) {
		this._parentNode = e, this.ownerDocument.markDirty(this);
	}
	get isConnected() {
		return this.parentNode?.isConnected || !1;
	}
	invalidateChildIndices(e) {
		(this._minInvalidChildIndex == null || !this._minInvalidChildIndex.isConnected || e.index < this._minInvalidChildIndex.index) && (this._minInvalidChildIndex = e, this.ownerDocument.markDirty(this));
	}
	updateChildIndices() {
		let e = this._minInvalidChildIndex;
		for (; e;) e.index = e.previousSibling ? e.previousSibling.index + 1 : 0, e = e.nextSibling;
		this._minInvalidChildIndex = null;
	}
	appendChild(e) {
		e.parentNode && e.parentNode.removeChild(e), this.firstChild ??= e, this.lastChild ? (this.lastChild.nextSibling = e, e.index = this.lastChild.index + 1, e.previousSibling = this.lastChild) : (e.previousSibling = null, e.index = 0), e.parentNode = this, e.nextSibling = null, this.lastChild = e, this.ownerDocument.markDirty(this), this.isConnected && this.ownerDocument.queueUpdate();
	}
	insertBefore(e, t) {
		if (t == null) return this.appendChild(e);
		e.parentNode && e.parentNode.removeChild(e), e.nextSibling = t, e.previousSibling = t.previousSibling, e.index = t.index - 1, this.firstChild === t ? this.firstChild = e : t.previousSibling && (t.previousSibling.nextSibling = e), t.previousSibling = e, e.parentNode = t.parentNode, this.invalidateChildIndices(e), this.isConnected && this.ownerDocument.queueUpdate();
	}
	removeChild(e) {
		e.parentNode === this && (this._minInvalidChildIndex === e && (this._minInvalidChildIndex = null), e.nextSibling && (this.invalidateChildIndices(e.nextSibling), e.nextSibling.previousSibling = e.previousSibling), e.previousSibling && (e.previousSibling.nextSibling = e.nextSibling), this.firstChild === e && (this.firstChild = e.nextSibling), this.lastChild === e && (this.lastChild = e.previousSibling), e.parentNode = null, e.nextSibling = null, e.previousSibling = null, e.index = 0, this.ownerDocument.markDirty(e), this.isConnected && this.ownerDocument.queueUpdate());
	}
	addEventListener() {}
	removeEventListener() {}
	get previousVisibleSibling() {
		let e = this.previousSibling;
		for (; e && e.isHidden;) e = e.previousSibling;
		return e;
	}
	get nextVisibleSibling() {
		let e = this.nextSibling;
		for (; e && e.isHidden;) e = e.nextSibling;
		return e;
	}
	get firstVisibleChild() {
		let e = this.firstChild;
		for (; e && e.isHidden;) e = e.nextSibling;
		return e;
	}
	get lastVisibleChild() {
		let e = this.lastChild;
		for (; e && e.isHidden;) e = e.previousSibling;
		return e;
	}
}, pt = class e extends ft {
	constructor(e, t) {
		super(t), this.nodeType = 8, this.isMutated = !0, this._index = 0, this.isHidden = !1, this.node = null;
	}
	get index() {
		return this._index;
	}
	set index(e) {
		this._index = e, this.ownerDocument.markDirty(this);
	}
	get level() {
		return this.parentNode instanceof e ? this.parentNode.level + +(this.parentNode.node?.type === "item") : 0;
	}
	getMutableNode() {
		return this.node == null ? null : (this.isMutated ||= (this.node = this.node.clone(), !0), this.ownerDocument.markDirty(this), this.node);
	}
	updateNode() {
		let t = this.nextVisibleSibling, n = this.getMutableNode();
		if (n != null && (n.index = this.index, n.level = this.level, n.parentKey = this.parentNode instanceof e ? this.parentNode.node?.key ?? null : null, n.prevKey = this.previousVisibleSibling?.node?.key ?? null, n.nextKey = t?.node?.key ?? null, n.hasChildNodes = !!this.firstChild, n.firstChildKey = this.firstVisibleChild?.node?.key ?? null, n.lastChildKey = this.lastVisibleChild?.node?.key ?? null, (n.colSpan != null || n.colIndex != null) && t)) {
			let e = (n.colIndex ?? n.index) + (n.colSpan ?? 1);
			if (t.node != null && e !== t.node.colIndex) {
				let n = t.getMutableNode();
				n.colIndex = e;
			}
		}
	}
	setProps(e, t, n, r, i) {
		let a, { value: o, textValue: s, id: c, ...l } = e;
		if (this.node == null ? (a = new n(c ?? `react-aria-${++this.ownerDocument.nodeId}`), this.node = a) : a = this.getMutableNode(), l.ref = t, a.props = l, a.rendered = r, a.render = i, a.value = o, e["aria-label"] && (a["aria-label"] = e["aria-label"]), a.textValue = s || (typeof l.children == "string" ? l.children : "") || e["aria-label"] || "", c != null && c !== a.key) throw Error("Cannot change the id of an item");
		l.colSpan != null && (a.colSpan = l.colSpan), this.isConnected && this.ownerDocument.queueUpdate();
	}
	get style() {
		let e = this;
		return {
			get display() {
				return e.isHidden ? "none" : "";
			},
			set display(t) {
				let n = t === "none";
				if (e.isHidden !== n) {
					(e.parentNode?.firstVisibleChild === e || e.parentNode?.lastVisibleChild === e) && e.ownerDocument.markDirty(e.parentNode);
					let t = e.previousVisibleSibling, r = e.nextVisibleSibling;
					t && e.ownerDocument.markDirty(t), r && e.ownerDocument.markDirty(r), e.isHidden = n, e.ownerDocument.markDirty(e);
				}
			}
		};
	}
	hasAttribute() {}
	setAttribute() {}
	setAttributeNS() {}
	removeAttribute() {}
}, mt = class extends ft {
	constructor(e) {
		super(null), this.nodeType = 11, this.ownerDocument = this, this.dirtyNodes = /* @__PURE__ */ new Set(), this.isSSR = !1, this.nodeId = 0, this.nodesByProps = /* @__PURE__ */ new WeakMap(), this.nextCollection = null, this.subscriptions = /* @__PURE__ */ new Set(), this.queuedRender = !1, this.inSubscription = !1, this.collection = e, this.nextCollection = e;
	}
	get isConnected() {
		return !0;
	}
	createElement(e) {
		return new pt(e, this);
	}
	getMutableCollection() {
		return this.nextCollection ||= this.collection.clone(), this.nextCollection;
	}
	markDirty(e) {
		this.dirtyNodes.add(e);
	}
	addNode(e) {
		if (e.isHidden || e.node == null) return;
		let t = this.getMutableCollection();
		if (!t.getItem(e.node.key)) for (let t of e) this.addNode(t);
		t.addNode(e.node);
	}
	removeNode(e) {
		for (let t of e) this.removeNode(t);
		e.node && this.getMutableCollection().removeNode(e.node.key);
	}
	getCollection() {
		return this.inSubscription ? this.collection : (this.queuedRender = !1, this.updateCollection(), this.collection);
	}
	updateCollection() {
		for (let e of this.dirtyNodes) e instanceof pt && (!e.isConnected || e.isHidden) ? this.removeNode(e) : e.updateChildIndices();
		for (let e of this.dirtyNodes) e instanceof pt ? (e.isConnected && !e.isHidden && (e.updateNode(), this.addNode(e)), e.node && this.dirtyNodes.delete(e), e.isMutated = !1) : this.dirtyNodes.delete(e);
		this.nextCollection && (this.nextCollection.commit(this.firstVisibleChild?.node?.key ?? null, this.lastVisibleChild?.node?.key ?? null, this.isSSR), this.isSSR || (this.collection = this.nextCollection, this.nextCollection = null));
	}
	queueUpdate() {
		if (!(this.dirtyNodes.size === 0 || this.queuedRender)) {
			this.queuedRender = !0, this.inSubscription = !0, this.isSSR || (this.collection = this.collection.clone());
			for (let e of this.subscriptions) e();
			this.inSubscription = !1;
		}
	}
	subscribe(e) {
		return this.subscriptions.add(e), this.queuedRender && e(), () => this.subscriptions.delete(e);
	}
	resetAfterSSR() {
		this.isSSR && (this.isSSR = !1, this.firstChild = null, this.lastChild = null, this.nodeId = 0);
	}
};
//#endregion
//#region node_modules/react-aria/dist/private/collections/useCachedChildren.mjs
function ht(e) {
	let { children: t, items: n, idScope: r, addIdAndValue: i, dependencies: a = [] } = e, o = (0, b.useMemo)(() => void 0, [t]), s = (0, b.useMemo)(() => /* @__PURE__ */ new WeakMap(), [...a, o]);
	return (0, b.useMemo)(() => {
		if (n && typeof t == "function") {
			let e = [];
			for (let a of n) {
				let n = gt(a) ? a : null, o = n ? s.get(n) : null;
				if (!o) {
					o = t(a);
					let c = o.props.id ?? a?.key ?? a?.id;
					r != null && o.props.id == null && c != null && (c = r + ":" + c);
					let l = c ?? e.length;
					o = (0, b.cloneElement)(o, i ? {
						key: l,
						id: c,
						value: a
					} : { key: l }), n && s.set(n, o);
				}
				e.push(o);
			}
			return e;
		}
		if (typeof t != "function") return t;
	}, [
		t,
		n,
		s,
		r,
		i
	]);
}
function gt(e) {
	switch (typeof e) {
		case "object": return e != null;
		case "function":
		case "symbol": return !0;
		default: return !1;
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/focusWithoutScrolling.mjs
function _t(e) {
	if (yt()) e.focus({ preventScroll: !0 });
	else {
		let t = bt(e);
		e.focus(), xt(t);
	}
}
var vt = null;
function yt() {
	if (vt == null) {
		vt = !1;
		try {
			document.createElement("div").focus({ get preventScroll() {
				return vt = !0, !0;
			} });
		} catch {}
	}
	return vt;
}
function bt(e) {
	let t = e.parentNode, n = [], r = document.scrollingElement || document.documentElement;
	for (; t instanceof HTMLElement && t !== r;) (t.offsetHeight < t.scrollHeight || t.offsetWidth < t.scrollWidth) && n.push({
		element: t,
		scrollTop: t.scrollTop,
		scrollLeft: t.scrollLeft
	}), t = t.parentNode;
	return r instanceof HTMLElement && n.push({
		element: r,
		scrollTop: r.scrollTop,
		scrollLeft: r.scrollLeft
	}), n;
}
function xt(e) {
	for (let { element: t, scrollTop: n, scrollLeft: r } of e) t.scrollTop = n, t.scrollLeft = r;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/domHelpers.mjs
var R = (e) => wt(e) ? e.document : Tt(e) ? e : e?.ownerDocument ?? (typeof document < "u" ? document : void 0), St = (e) => R(e)?.defaultView ?? (typeof window < "u" ? window : void 0);
function Ct(e) {
	return typeof e == "object" && !!e && "nodeType" in e && typeof e.nodeType == "number";
}
function wt(e) {
	return typeof e == "object" && !!e && "window" in e && e.window === e;
}
function Tt(e) {
	return Ct(e) && e.nodeType === 9;
}
function Et(e) {
	return Ct(e) && e.nodeType === 11 && "host" in e;
}
function Dt(e, t, n, r) {
	if (n == null || e == null) return () => {};
	let i = Array.isArray(e) ? e : [e];
	for (let e of i) e.addEventListener(t, n, r);
	return () => {
		for (let e of i) e.removeEventListener(t, n, r);
	};
}
function Ot(e, t, n, r) {
	if (e == null) return () => {};
	let i = [], a = Array.isArray(e) ? e : [e];
	for (let e of a) {
		let a = e.style.getPropertyValue(t), o = e.style.getPropertyPriority(t);
		e.style.setProperty(t, n, r), i.unshift(() => {
			a ? e.style.setProperty(t, a, o) : e.style.removeProperty(t);
		});
	}
	return () => {
		for (let e of i) e();
	};
}
//#endregion
//#region node_modules/react-stately/dist/private/flags/flags.mjs
var kt = !1;
function At() {
	return kt;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/shadowdom/DOMFunctions.mjs
function z(e, t) {
	if (!At()) return t && e ? e.contains(t) : !1;
	if (!e || !t) return !1;
	let n = t;
	for (; n !== null;) {
		if (n === e) return !0;
		n = typeof n.assignedElements != "function" && n.assignedSlot?.parentNode ? n.assignedSlot.parentNode : Et(n) ? n.host : n.parentNode;
	}
	return !1;
}
var jt = (e = document) => {
	if (!At()) return e.activeElement;
	let t = e.activeElement;
	for (; t && "shadowRoot" in t && t.shadowRoot?.activeElement;) t = t.shadowRoot.activeElement;
	return t;
};
function B(e) {
	if (At() && e.target instanceof Element && e.target.shadowRoot) {
		if ("composedPath" in e) return e.composedPath()[0] ?? null;
		if ("composedPath" in e.nativeEvent) return e.nativeEvent.composedPath()[0] ?? null;
	}
	return e.target;
}
function Mt(e, t) {
	if (t === null) return [];
	t ??= St(e);
	let n = [t];
	if (!At() || !e || e === t) return n;
	let r = "getRootNode" in t ? t.getRootNode() : null, i = e.getRootNode() ?? null;
	for (; Et(i) && i !== r;) n.push(i), i = i.host.getRootNode();
	return n;
}
function Nt(e) {
	if (!e) return !1;
	let t = e.getRootNode(), n = St(e);
	if (!(t instanceof n.Document || t instanceof n.ShadowRoot)) return !1;
	let r = t.activeElement;
	return r != null && e.contains(r);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/isElementVisible.mjs
var Pt = typeof Element < "u" && "checkVisibility" in Element.prototype;
function Ft(e) {
	let t = St(e);
	if (!(e instanceof t.HTMLElement) && !(e instanceof t.SVGElement)) return !1;
	let { display: n, visibility: r } = e.style, i = n !== "none" && r !== "hidden" && r !== "collapse";
	if (i) {
		let { getComputedStyle: t } = St(e), { display: n, visibility: r } = t(e);
		i = n !== "none" && r !== "hidden" && r !== "collapse";
	}
	return i;
}
function It(e, t) {
	return !e.hasAttribute("hidden") && !e.hasAttribute("data-react-aria-prevent-focus") && (e.nodeName === "DETAILS" && t && t.nodeName !== "SUMMARY" ? e.hasAttribute("open") : !0);
}
function Lt(e, t) {
	return Pt ? e.checkVisibility({ visibilityProperty: !0 }) && !e.closest("[data-react-aria-prevent-focus]") : e.nodeName !== "#comment" && Ft(e) && It(e, t) && (!e.parentElement || Lt(e.parentElement, e));
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/isFocusable.mjs
var Rt = [
	"input:not([disabled]):not([type=hidden])",
	"select:not([disabled])",
	"textarea:not([disabled])",
	"button:not([disabled])",
	"a[href]",
	"area[href]",
	"summary",
	"iframe",
	"object",
	"embed",
	"audio[controls]",
	"video[controls]",
	"[contenteditable]:not([contenteditable^=\"false\"])",
	"permission"
], zt = Rt.join(":not([hidden]),") + ",[tabindex]:not([disabled]):not([hidden])";
Rt.push("[tabindex]:not([tabindex=\"-1\"]):not([disabled])");
var Bt = Rt.join(":not([hidden]):not([tabindex=\"-1\"]),");
function Vt(e, t) {
	return e.matches(zt) && !Ht(e) && (t?.skipVisibilityCheck || Lt(e));
}
function V(e) {
	return e.matches(Bt) && Lt(e) && !Ht(e);
}
function Ht(e) {
	let t = e;
	for (; t != null;) {
		if (t instanceof St(t).HTMLElement && t.inert) return !0;
		t = t.parentElement;
	}
	return !1;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useLayoutEffect.mjs
var H = typeof document < "u" ? b.useLayoutEffect : () => {};
//#endregion
//#region node_modules/react-aria/dist/private/interactions/utils.mjs
function Ut(e) {
	let t = e;
	return t.nativeEvent = e, t.isDefaultPrevented = () => t.defaultPrevented, t.isPropagationStopped = () => t.cancelBubble, t.persist = () => {}, t;
}
function Wt(e, t) {
	Object.defineProperty(e, "target", { value: t }), Object.defineProperty(e, "currentTarget", { value: t });
}
function Gt(e) {
	let t = (0, b.useRef)({
		isFocused: !1,
		observer: null
	});
	return H(() => {
		let e = t.current;
		return () => {
			e.observer &&= (e.observer.disconnect(), null);
		};
	}, []), (0, b.useCallback)((n) => {
		let r = B(n);
		if (r instanceof HTMLButtonElement || r instanceof HTMLInputElement || r instanceof HTMLTextAreaElement || r instanceof HTMLSelectElement) {
			t.current.isFocused = !0;
			let n = r;
			n.addEventListener("focusout", (r) => {
				if (t.current.isFocused = !1, n.disabled) {
					let t = Ut(r);
					e?.(t);
				}
				t.current.observer && (t.current.observer.disconnect(), t.current.observer = null);
			}, { once: !0 }), t.current.observer = new MutationObserver(() => {
				if (t.current.isFocused && n.disabled) {
					t.current.observer?.disconnect();
					let e = n === jt() ? null : jt();
					n.dispatchEvent(new FocusEvent("blur", { relatedTarget: e })), n.dispatchEvent(new FocusEvent("focusout", {
						bubbles: !0,
						relatedTarget: e
					}));
				}
			}), t.current.observer.observe(n, {
				attributes: !0,
				attributeFilter: ["disabled"]
			});
		}
	}, [e]);
}
var Kt = !1;
function qt(e) {
	for (; e && !Vt(e, { skipVisibilityCheck: !0 });) e = e.parentElement;
	let t = jt(St(e).document);
	if (!t || t === e) return;
	let n = e?.getRootNode(), r = n != null && Et(n) ? n : St(e), i = (t) => t === e || t != null && z(e, t), a = (e) => e === t || t != null && e != null && z(t, e);
	Kt = !0;
	let o = !1, s = (e) => {
		(a(B(e)) || o) && e.stopImmediatePropagation();
	}, c = (n) => {
		(a(B(n)) || o) && (n.stopImmediatePropagation(), !e && !o && (o = !0, _t(t), d()));
	}, l = (e) => {
		(i(B(e)) || o) && e.stopImmediatePropagation();
	}, u = (e) => {
		(i(B(e)) || o) && (e.stopImmediatePropagation(), o || (o = !0, _t(t), d()));
	};
	r.addEventListener("blur", s, !0), r.addEventListener("focusout", c, !0), r.addEventListener("focusin", u, !0), r.addEventListener("focus", l, !0);
	let d = () => {
		cancelAnimationFrame(f), r.removeEventListener("blur", s, !0), r.removeEventListener("focusout", c, !0), r.removeEventListener("focusin", u, !0), r.removeEventListener("focus", l, !0), Kt = !1, o = !1;
	}, f = requestAnimationFrame(d);
	return d;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/platform.mjs
function Jt(e) {
	if (typeof window > "u" || window.navigator == null) return !1;
	let t = window.navigator.userAgentData?.brands;
	return Array.isArray(t) && t.some((t) => e.test(t.brand)) || e.test(window.navigator.userAgent);
}
function Yt(e) {
	return typeof window < "u" && window.navigator != null && e.test(window.navigator.userAgentData?.platform || window.navigator.platform);
}
function Xt(e) {
	let t = null;
	return () => (t ??= e(), t);
}
var Zt = Xt(function() {
	return Yt(/^Mac/i);
}), Qt = Xt(function() {
	return Yt(/^iPhone/i);
}), $t = Xt(function() {
	return Yt(/^iPad/i) || Zt() && navigator.maxTouchPoints > 1;
}), en = Xt(function() {
	return Qt() || $t();
}), tn = Xt(function() {
	return Zt() || en();
}), nn = Xt(function() {
	return Jt(/AppleWebKit/i) && (en() || !rn());
}), rn = Xt(function() {
	return Jt(/Chrome|CriOS|CrMo/i);
}), an = Xt(function() {
	return Jt(/Android/i);
}), on = Xt(function() {
	return Jt(/(Firefox|FxiOS)/i);
});
//#endregion
//#region node_modules/react-aria/dist/private/utils/isVirtualEvent.mjs
function sn(e) {
	return e.pointerType === "" && e.isTrusted ? !0 : an() && e.pointerType ? e.type === "click" && e.buttons === 1 : e.detail === 0 && !e.pointerType;
}
function cn(e) {
	return !an() && e.width === 0 && e.height === 0 || an() && e.width === 1 && e.height === 1 && e.pressure === 0 && e.detail === 0 && e.pointerType === "mouse";
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/openLink.mjs
var ln = /*#__PURE__*/ (0, b.createContext)({
	isNative: !0,
	open: pn,
	useHref: (e) => e
});
function un() {
	return (0, b.useContext)(ln);
}
function dn(e, t, n = !0) {
	let { metaKey: r, ctrlKey: i, altKey: a, shiftKey: o } = t;
	!nn() && on() && window.event?.type?.startsWith("key") && e.target === "_blank" && (Zt() ? r = !0 : i = !0);
	let s = nn() && Zt() && !$t() ? new KeyboardEvent("keydown", {
		keyIdentifier: "Enter",
		metaKey: r,
		ctrlKey: i,
		altKey: a,
		shiftKey: o
	}) : new MouseEvent("click", {
		metaKey: r,
		ctrlKey: i,
		altKey: a,
		shiftKey: o,
		detail: 1,
		bubbles: !0,
		cancelable: !0
	});
	dn.isOpening = n, _t(e), e.dispatchEvent(s), dn.isOpening = !1;
}
dn.isOpening = !1;
function fn(e, t) {
	if (e instanceof HTMLAnchorElement) t(e);
	else if (e.hasAttribute("data-href")) {
		let n = document.createElement("a");
		n.href = e.getAttribute("data-href"), e.hasAttribute("data-target") && (n.target = e.getAttribute("data-target")), e.hasAttribute("data-rel") && (n.rel = e.getAttribute("data-rel")), e.hasAttribute("data-download") && (n.download = e.getAttribute("data-download")), e.hasAttribute("data-ping") && (n.ping = e.getAttribute("data-ping")), e.hasAttribute("data-referrer-policy") && (n.referrerPolicy = e.getAttribute("data-referrer-policy")), e.appendChild(n), t(n), e.removeChild(n);
	}
}
function pn(e, t) {
	fn(e, (e) => dn(e, t));
}
function mn(e) {
	let t = un().useHref(e?.href ?? ""), n = {};
	if (e) for (let r of [
		"href",
		"target",
		"rel",
		"download",
		"ping",
		"referrerPolicy"
	]) r in e && e[r] !== void 0 && (n[r] = r === "href" ? t : e[r]);
	return n;
}
//#endregion
//#region node_modules/react-aria/dist/private/ssr/SSRProvider.mjs
var hn = {
	prefix: String(Math.round(Math.random() * 1e10)),
	current: 0
}, gn = /*#__PURE__*/ b.createContext(hn), _n = /*#__PURE__*/ b.createContext(!1);
typeof window < "u" && window.document && window.document.createElement;
var vn = /* @__PURE__ */ new WeakMap();
function yn(e = !1) {
	let t = (0, b.useContext)(gn), n = (0, b.useRef)(null);
	if (n.current === null && !e) {
		let e = b.default.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED?.ReactCurrentOwner?.current;
		if (e) {
			let n = vn.get(e);
			n == null ? vn.set(e, {
				id: t.current,
				state: e.memoizedState
			}) : e.memoizedState !== n.state && (t.current = n.id, vn.delete(e));
		}
		n.current = ++t.current;
	}
	return n.current;
}
function bn(e) {
	let t = (0, b.useContext)(gn), n = yn(!!e), r = `react-aria${t.prefix}`;
	return e || `${r}-${n}`;
}
function xn(e) {
	let t = b.useId(), [n] = (0, b.useState)(En()), r = n ? "react-aria" : `react-aria${hn.prefix}`;
	return e || `${r}-${t}`;
}
var Sn = typeof b.useId == "function" ? xn : bn;
function Cn() {
	return !1;
}
function wn() {
	return !0;
}
function Tn(e) {
	return () => {};
}
function En() {
	return typeof b.useSyncExternalStore == "function" ? b.useSyncExternalStore(Tn, Cn, wn) : (0, b.useContext)(_n);
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocusVisible.mjs
var Dn = null, On = /* @__PURE__ */ new Set(), kn = /* @__PURE__ */ new Map(), An = !1, jn = !1, Mn = {
	Tab: !0,
	Escape: !0
};
function Nn(e, t) {
	for (let n of On) n(e, t);
}
function Pn(e) {
	return !(e.metaKey || !Zt() && e.altKey || e.ctrlKey || e.key === "Control" || e.key === "Shift" || e.key === "Meta");
}
function Fn(e) {
	An = !0, !dn.isOpening && Pn(e) && (Dn = "keyboard", Nn("keyboard", e));
}
function In(e) {
	Dn = "pointer", "pointerType" in e && e.pointerType, (e.type === "mousedown" || e.type === "pointerdown") && (An = !0, Nn("pointer", e));
}
function Ln(e) {
	!dn.isOpening && sn(e) && (An = !0, Dn = "virtual");
}
function Rn(e) {
	if (Kt) return;
	let t = B(e), n = St(t), r = R(t);
	if (t === n) {
		jn = !0;
		return;
	}
	t === r || !e.isTrusted || (!An && !jn && (Dn = "virtual", Nn("virtual", e)), An = !1, jn = !1);
}
function zn() {
	Kt || (An = !1, jn = !0);
}
function Bn(e) {
	if (typeof window > "u" || typeof document > "u") return;
	let t = St(e), n = R(e);
	if (kn.get(t)) return;
	let r = t.HTMLElement.prototype.focus;
	Reflect.defineProperty(t.HTMLElement.prototype, "focus", {
		configurable: !0,
		writable: !0,
		value: function() {
			An = !0, r.apply(this, arguments);
		}
	}), n.addEventListener("keydown", Fn, !0), n.addEventListener("keyup", Fn, !0), n.addEventListener("click", Ln, !0), t.addEventListener("focus", Rn, !0), t.addEventListener("blur", zn, !1), typeof PointerEvent < "u" && (n.addEventListener("pointerdown", In, !0), n.addEventListener("pointermove", In, !0), n.addEventListener("pointerup", In, !0)), t.addEventListener("beforeunload", () => {
		Vn(e);
	}, { once: !0 }), kn.set(t, { focus: r });
}
var Vn = (e, t) => {
	let n = St(e), r = R(e);
	t && r.removeEventListener("DOMContentLoaded", t), kn.has(n) && (Reflect.defineProperty(n.HTMLElement.prototype, "focus", {
		configurable: !0,
		writable: !0,
		value: kn.get(n).focus
	}), r.removeEventListener("keydown", Fn, !0), r.removeEventListener("keyup", Fn, !0), r.removeEventListener("click", Ln, !0), n.removeEventListener("focus", Rn, !0), n.removeEventListener("blur", zn, !1), typeof PointerEvent < "u" && (r.removeEventListener("pointerdown", In, !0), r.removeEventListener("pointermove", In, !0), r.removeEventListener("pointerup", In, !0)), kn.delete(n));
};
function Hn(e) {
	let t = R(e), n;
	return t.readyState === "loading" ? (n = () => {
		Bn(e);
	}, t.addEventListener("DOMContentLoaded", n)) : Bn(e), () => Vn(e, n);
}
typeof document < "u" && Hn();
function Un() {
	return Dn !== "pointer";
}
function Wn() {
	return Dn;
}
function Gn(e) {
	Dn = e, Nn(e, null);
}
var Kn = /* @__PURE__ */ new Set([
	"checkbox",
	"radio",
	"range",
	"color",
	"file",
	"image",
	"button",
	"submit",
	"reset"
]);
function qn(e, t, n) {
	let r = n ? B(n) : void 0, i = R(r), a = St(r), o = a === void 0 ? HTMLInputElement : a.HTMLInputElement, s = a === void 0 ? HTMLTextAreaElement : a.HTMLTextAreaElement, c = a === void 0 ? HTMLElement : a.HTMLElement, l = a === void 0 ? KeyboardEvent : a.KeyboardEvent, u = jt(i);
	return e = e || u instanceof o && !Kn.has(u.type) || u instanceof s || u instanceof c && u.isContentEditable, !(e && t === "keyboard" && n instanceof l && !Mn[n.key]);
}
function Jn(e, t, n) {
	Bn(), (0, b.useEffect)(() => {
		if (n?.enabled === !1) return;
		let t = (t, r) => {
			qn(!!n?.isTextInput, t, r) && e(Un());
		};
		return On.add(t), () => {
			On.delete(t);
		};
	}, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/runAfterTransition.mjs
var Yn = /* @__PURE__ */ new Map(), Xn = /* @__PURE__ */ new Set();
function Zn() {
	if (typeof window > "u") return;
	function e(e) {
		return "propertyName" in e;
	}
	let t = (t) => {
		let r = B(t);
		if (!e(t) || !r) return;
		let i = Yn.get(r);
		i || (i = /* @__PURE__ */ new Set(), Yn.set(r, i), r.addEventListener("transitioncancel", n, { once: !0 })), i.add(t.propertyName);
	}, n = (t) => {
		let r = B(t);
		if (!e(t) || !r) return;
		let i = Yn.get(r);
		if (i && (i.delete(t.propertyName), i.size === 0 && (r.removeEventListener("transitioncancel", n), Yn.delete(r)), Yn.size === 0)) {
			for (let e of Xn) e();
			Xn.clear();
		}
	};
	document.body.addEventListener("transitionrun", t), document.body.addEventListener("transitionend", n);
}
typeof document < "u" && (document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", Zn) : Zn());
function Qn() {
	for (let [e] of Yn) "isConnected" in e && !e.isConnected && Yn.delete(e);
}
function $n(e) {
	requestAnimationFrame(() => {
		Qn(), Yn.size === 0 ? e() : Xn.add(e);
	});
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/focusSafely.mjs
function er(e) {
	if (!e.isConnected) return;
	let t = R(e);
	if (Wn() === "virtual") {
		let n = jt(t);
		$n(() => {
			let r = jt(t);
			(r === n || r === t.body) && e.isConnected && _t(e);
		});
	} else _t(e);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/chain.mjs
function tr(...e) {
	return (...t) => {
		for (let n of e) typeof n == "function" && n(...t);
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useValueEffect.mjs
function nr(e) {
	let [t, n] = (0, b.useState)(e), r = (0, b.useRef)(t), i = (0, b.useRef)(null), a = (0, b.useRef)(() => {
		if (!i.current) return;
		let e = i.current.next();
		if (e.done) {
			i.current = null;
			return;
		}
		r.current === e.value ? a.current() : n(e.value);
	});
	return H(() => {
		r.current = t, i.current && a.current();
	}), [t, (0, b.useCallback)((e) => {
		i.current = e(r.current), a.current();
	}, [a])];
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useId.mjs
var rr = !!(typeof window < "u" && window.document && window.document.createElement), ir = /* @__PURE__ */ new Map(), ar;
typeof FinalizationRegistry < "u" && (ar = new FinalizationRegistry((e) => {
	ir.delete(e);
}));
var or = /* @__PURE__ */ new WeakMap();
function sr(e) {
	let [t, n] = (0, b.useState)(e), r = (0, b.useRef)(null), i = Sn(t), a = (0, b.useRef)(null), o = or.get(a);
	if (ar && o !== i && (o != null && ar.unregister(a), ar.register(a, i, a), or.set(a, i)), rr) {
		let e = ir.get(i);
		e && !e.includes(r) ? e.push(r) : ir.set(i, [r]);
	}
	return H(() => {
		let e = i;
		return () => {
			ar && (ar.unregister(a), or.delete(a)), ir.delete(e);
		};
	}, [i]), (0, b.useEffect)(() => {
		let e = r.current;
		return e && n(e), () => {
			e && (r.current = null);
		};
	}), i;
}
function cr(e, t) {
	if (e === t) return e;
	let n = ir.get(e);
	if (n) return n.forEach((e) => e.current = t), t;
	let r = ir.get(t);
	return r ? (r.forEach((t) => t.current = e), e) : t;
}
function lr(e = []) {
	let t = sr(), [n, r] = nr(t), i = (0, b.useCallback)(() => {
		r(function* () {
			yield t, yield document.getElementById(t) ? t : void 0;
		});
	}, [t, r]);
	return H(i, [
		t,
		i,
		...e
	]), n;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/mergeRefs.mjs
function ur(...e) {
	return e.length === 1 && e[0] ? e[0] : (t) => {
		let n = !1, r = e.map((e) => {
			let r = dr(e, t);
			return n ||= typeof r == "function", r;
		});
		if (n) return () => {
			r.forEach((t, n) => {
				typeof t == "function" ? t() : dr(e[n], null);
			});
		};
	};
}
function dr(e, t) {
	if (typeof e == "function") return e(t);
	e != null && (e.current = t);
}
//#endregion
//#region node_modules/clsx/dist/clsx.mjs
function fr(e) {
	var t, n, r = "";
	if (typeof e == "string" || typeof e == "number") r += e;
	else if (typeof e == "object") {
		if (Array.isArray(e)) {
			var i = e.length;
			for (t = 0; t < i; t++) e[t] && (n = fr(e[t])) && (r && (r += " "), r += n);
		} else for (n in e) e[n] && (r && (r += " "), r += n);
	}
	return r;
}
function pr() {
	for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = fr(e)) && (r && (r += " "), r += t);
	return r;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/mergeProps.mjs
function U(...e) {
	let t = { ...e[0] };
	for (let n = 1; n < e.length; n++) {
		let r = e[n];
		for (let e in r) {
			let n = t[e], i = r[e];
			typeof n == "function" && typeof i == "function" && e[0] === "o" && e[1] === "n" && e.charCodeAt(2) >= 65 && e.charCodeAt(2) <= 90 ? t[e] = tr(n, i) : (e === "className" || e === "UNSAFE_className") && typeof n == "string" && typeof i == "string" ? t[e] = pr(n, i) : e === "id" && n && i ? t.id = cr(n, i) : e === "ref" && n && i ? t.ref = ur(n, i) : t[e] = i === void 0 ? n : i;
		}
	}
	return t;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocus.mjs
function mr(e) {
	let { isDisabled: t, onFocus: n, onBlur: r, onFocusChange: i } = e, a = (0, b.useCallback)((e) => {
		if (B(e) === e.currentTarget) return r && r(e), i && i(!1), !0;
	}, [r, i]), o = Gt(a), s = (0, b.useCallback)((e) => {
		let t = B(e), r = R(t), a = r ? jt(r) : jt();
		t === e.currentTarget && t === a && (n && n(e), i && i(!0), o(e));
	}, [
		i,
		n,
		o
	]);
	return { focusProps: {
		onFocus: !t && (n || i || r) ? s : void 0,
		onBlur: !t && (r || i) ? a : void 0
	} };
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/createEventHandler.mjs
function hr(e) {
	if (e) return (t) => {
		let n = !0;
		e({
			...t,
			preventDefault() {
				t.preventDefault();
			},
			isDefaultPrevented() {
				return t.isDefaultPrevented();
			},
			stopPropagation() {
				n = !0;
			},
			continuePropagation() {
				n = !1, typeof t.continuePropagation == "function" && t.continuePropagation();
			},
			isPropagationStopped() {
				return n;
			}
		}), n && !(typeof t.isPropagationStopped == "function" && t.isPropagationStopped()) && t.stopPropagation();
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/createKeyboardShortcutHandler.mjs
var gr = /* @__PURE__ */ new Set([
	"shift",
	"alt",
	"control",
	"meta",
	"mod"
]), _r = [
	"Alt",
	"Control",
	"Meta",
	"Shift"
];
function vr(e) {
	let t = /* @__PURE__ */ new Set();
	return e.alt && t.add("Alt"), e.shift && t.add("Shift"), e.ctrl && t.add("Control"), e.meta && t.add("Meta"), e.mod && t.add(Zt() ? "Meta" : "Control"), t;
}
function yr(e) {
	let t = /* @__PURE__ */ new Set();
	return e.altKey && t.add("Alt"), e.ctrlKey && t.add("Control"), e.metaKey && t.add("Meta"), e.shiftKey && t.add("Shift"), t;
}
function br(e) {
	return _r.filter((t) => e.has(t));
}
function xr(e) {
	let t = e.split("+").reduce((e, t) => {
		let n = t.toLowerCase();
		return gr.has(n) ? n === "shift" ? e.shift = !0 : n === "alt" ? e.alt = !0 : n === "control" ? e.ctrl = !0 : n === "meta" ? e.meta = !0 : n === "mod" && (e.mod = !0) : e.key = t, e;
	}, {
		shift: !1,
		alt: !1,
		ctrl: !1,
		meta: !1,
		mod: !1,
		key: ""
	});
	if (t.key === "") throw Error(`Invalid keyboard shortcut: "${e}". Must include exactly one non-modifier key (e.g. "a", "Enter", "ArrowDown"). Combine any of Shift, Alt, Ctrl, Meta, and Mod.`);
	return t;
}
function Sr(e) {
	return e.toLowerCase();
}
var Cr = {
	space: " ",
	esc: "escape",
	del: "delete",
	ins: "insert",
	left: "arrowleft",
	right: "arrowright",
	up: "arrowup",
	down: "arrowdown",
	pageup: "pageup",
	pagedown: "pagedown"
};
function wr(e) {
	let t = Sr(e);
	return Cr[t] ?? t;
}
function Tr(e) {
	let t = br(vr(e)), n = wr(e.key);
	return t.length > 0 ? `${t.join("+")}+${n}` : n;
}
function Er(e) {
	let t = br(yr(e)), n = Sr(e.key);
	return (t.length > 0 ? `${t.join("+")}+` : "") + n;
}
function Dr(e) {
	let t = /* @__PURE__ */ new Map();
	for (let [n, r] of Object.entries(e)) {
		let e = xr(n);
		t.set(Tr(e), r);
	}
	return (e) => {
		let n = Er(e), r = t.get(n), i = r?.(e);
		i === void 0 && r !== void 0 ? i = {
			shouldContinuePropagation: !1,
			shouldPreventDefault: !0
		} : typeof i == "boolean" && (i = {
			shouldContinuePropagation: !i,
			shouldPreventDefault: i
		}), i?.shouldPreventDefault && e.preventDefault(), (!r || i?.shouldContinuePropagation) && e.continuePropagation();
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useKeyboard.mjs
function Or(e) {
	let { shortcuts: t, allowRepeats: n = !1, allowComposing: r = !1 } = e, i, a;
	if (t) {
		let o = Dr(t), s = hr((e) => {
			if (!z(e.currentTarget, B(e))) {
				e.continuePropagation();
				return;
			}
			if (e.nativeEvent?.repeat && !n || e.nativeEvent?.isComposing && !r) {
				e.continuePropagation();
				return;
			}
			o(e);
		}), c = hr((e) => {
			if (!z(e.currentTarget, B(e))) {
				e.continuePropagation();
				return;
			}
			if (e.nativeEvent?.repeat && !n || e.nativeEvent?.isComposing && !r) {
				e.continuePropagation();
				return;
			}
			e.continuePropagation();
		});
		i = e.onKeyDown ? tr(e.onKeyDown, s) : s, a = e.onKeyUp ? tr(e.onKeyUp, c) : c;
	} else i = hr(e.onKeyDown), a = hr(e.onKeyUp);
	return { keyboardProps: e.isDisabled ? {} : {
		onKeyDown: i,
		onKeyUp: a
	} };
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useObjectRef.mjs
function kr(e) {
	let t = (0, b.useRef)(null), n = (0, b.useRef)(void 0), r = (0, b.useCallback)((t) => {
		if (typeof e == "function") {
			let n = e, r = n(t);
			return () => {
				typeof r == "function" ? r() : n(null);
			};
		}
		if (e) return e.current = t, () => {
			e.current = null;
		};
	}, [e]);
	return (0, b.useMemo)(() => ({
		get current() {
			return t.current;
		},
		set current(e) {
			t.current = e, n.current &&= (n.current(), void 0), e != null && (n.current = r(e));
		}
	}), [r]);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useSyncRef.mjs
function Ar(e, t) {
	H(() => {
		if (e && e.ref && t) return e.ref.current = t.current, () => {
			e.ref && (e.ref.current = null);
		};
	});
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocusable.mjs
var jr = /*#__PURE__*/ b.createContext(null);
function Mr(e) {
	let t = (0, b.useContext)(jr) || {};
	Ar(t, e);
	let { ref: n, ...r } = t;
	return r;
}
function Nr(e, t) {
	let { focusProps: n } = mr(e), { keyboardProps: r } = Or(e), i = U(n, r), a = Mr(t), o = e.isDisabled ? {} : a, s = (0, b.useRef)(e.autoFocus);
	(0, b.useEffect)(() => {
		s.current && t.current && er(t.current), s.current = !1;
	}, [t]);
	let c = e.excludeFromTabOrder ? -1 : 0;
	return e.isDisabled && (c = void 0), { focusableProps: U({
		...i,
		tabIndex: c
	}, o) };
}
//#endregion
//#region node_modules/react-aria/dist/private/collections/Hidden.mjs
typeof HTMLTemplateElement < "u" && (Object.defineProperty(HTMLTemplateElement.prototype, "firstChild", {
	configurable: !0,
	enumerable: !0,
	get: function() {
		return this.content.firstChild;
	}
}), Object.defineProperty(HTMLTemplateElement.prototype, "appendChild", {
	configurable: !0,
	enumerable: !0,
	value: function(e) {
		return this.content.appendChild(e);
	}
}), Object.defineProperty(HTMLTemplateElement.prototype, "removeChild", {
	configurable: !0,
	enumerable: !0,
	value: function(e) {
		return this.content.removeChild(e);
	}
}), Object.defineProperty(HTMLTemplateElement.prototype, "insertBefore", {
	configurable: !0,
	enumerable: !0,
	value: function(e, t) {
		return this.content.insertBefore(e, t);
	}
}));
var Pr = /*#__PURE__*/ (0, b.createContext)(!1);
function Fr(e) {
	if ((0, b.useContext)(Pr)) return /*#__PURE__*/ b.createElement(b.Fragment, null, e.children);
	let t = /*#__PURE__*/ b.createElement(Pr.Provider, { value: !0 }, e.children);
	return /*#__PURE__*/ b.createElement("template", null, t);
}
function Ir(e) {
	let t = (t, n) => (0, b.useContext)(Pr) ? null : e(t, n);
	return t.displayName = e.displayName || e.name, (0, b.forwardRef)(t);
}
function Lr() {
	return (0, b.useContext)(Pr);
}
//#endregion
//#region node_modules/react-dom/cjs/react-dom.production.js
var Rr = /* @__PURE__ */ p(((e) => {
	var t = _();
	function n(e) {
		var t = "https://react.dev/errors/" + e;
		if (1 < arguments.length) {
			t += "?args[]=" + encodeURIComponent(arguments[1]);
			for (var n = 2; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
		}
		return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
	}
	function r() {}
	var i = {
		d: {
			f: r,
			r: function() {
				throw Error(n(522));
			},
			D: r,
			C: r,
			L: r,
			m: r,
			X: r,
			S: r,
			M: r
		},
		p: 0,
		findDOMNode: null
	}, a = Symbol.for("react.portal"), o = Symbol.for("react.recoverable"), s = Symbol.for("react.optimistic_key");
	function c(e, t, n) {
		var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
		return {
			$$typeof: a,
			key: r == null ? null : r === s ? s : "" + r,
			children: e,
			containerInfo: t,
			implementation: n
		};
	}
	var l = t.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE;
	function u(e, t) {
		if (e === "font") return "";
		if (typeof t == "string") return t === "use-credentials" ? t : "";
	}
	e.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = i, e.browser = function(e) {
		return {
			$$typeof: o,
			_reason: e
		};
	}, e.createPortal = function(e, t) {
		var r = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
		if (!t || t.nodeType !== 1 && t.nodeType !== 9 && t.nodeType !== 11) throw Error(n(299));
		return c(e, t, null, r);
	}, e.flushSync = function(e) {
		var t = l.T, n = i.p;
		try {
			if (l.T = null, i.p = 2, e) return e();
		} finally {
			l.T = t, i.p = n, i.d.f();
		}
	}, e.preconnect = function(e, t) {
		typeof e == "string" && (t ? (t = t.crossOrigin, t = typeof t == "string" ? t === "use-credentials" ? t : "" : void 0) : t = null, i.d.C(e, t));
	}, e.prefetchDNS = function(e) {
		typeof e == "string" && i.d.D(e);
	}, e.preinit = function(e, t) {
		if (typeof e == "string" && t && typeof t.as == "string") {
			var n = t.as, r = u(n, t.crossOrigin), a = typeof t.integrity == "string" ? t.integrity : void 0, o = typeof t.fetchPriority == "string" ? t.fetchPriority : void 0;
			n === "style" ? i.d.S(e, typeof t.precedence == "string" ? t.precedence : void 0, {
				crossOrigin: r,
				integrity: a,
				fetchPriority: o
			}) : n === "script" && i.d.X(e, {
				crossOrigin: r,
				integrity: a,
				fetchPriority: o,
				nonce: typeof t.nonce == "string" ? t.nonce : void 0
			});
		}
	}, e.preinitModule = function(e, t) {
		if (typeof e == "string") {
			if (typeof t == "object" && t) {
				if (t.as == null || t.as === "script") {
					var n = u(t.as, t.crossOrigin);
					i.d.M(e, {
						crossOrigin: n,
						integrity: typeof t.integrity == "string" ? t.integrity : void 0,
						nonce: typeof t.nonce == "string" ? t.nonce : void 0,
						fetchPriority: typeof t.fetchPriority == "string" ? t.fetchPriority : void 0
					});
				}
			} else t ?? i.d.M(e);
		}
	}, e.preload = function(e, t) {
		if (typeof e == "string" && typeof t == "object" && t && typeof t.as == "string") {
			var n = t.as, r = u(n, t.crossOrigin);
			i.d.L(e, n, {
				crossOrigin: r,
				integrity: typeof t.integrity == "string" ? t.integrity : void 0,
				nonce: typeof t.nonce == "string" ? t.nonce : void 0,
				type: typeof t.type == "string" ? t.type : void 0,
				fetchPriority: typeof t.fetchPriority == "string" ? t.fetchPriority : void 0,
				referrerPolicy: typeof t.referrerPolicy == "string" ? t.referrerPolicy : void 0,
				imageSrcSet: typeof t.imageSrcSet == "string" ? t.imageSrcSet : void 0,
				imageSizes: typeof t.imageSizes == "string" ? t.imageSizes : void 0,
				media: typeof t.media == "string" ? t.media : void 0
			});
		}
	}, e.preloadModule = function(e, t) {
		if (typeof e == "string") {
			if (t) {
				var n = u(t.as, t.crossOrigin);
				i.d.m(e, {
					as: typeof t.as == "string" && t.as !== "script" ? t.as : void 0,
					crossOrigin: n,
					integrity: typeof t.integrity == "string" ? t.integrity : void 0,
					nonce: typeof t.nonce == "string" ? t.nonce : void 0,
					fetchPriority: typeof t.fetchPriority == "string" ? t.fetchPriority : void 0
				});
			} else i.d.m(e);
		}
	}, e.requestFormReset = function(e) {
		i.d.r(e);
	}, e.unstable_batchedUpdates = function(e, t) {
		return e(t);
	}, e.useFormState = function(e, t, n) {
		return l.H.useFormState(e, t, n);
	}, e.useFormStatus = function() {
		return l.H.useHostTransitionStatus();
	}, e.version = "19.3.0";
})), zr = /* @__PURE__ */ p(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = Rr();
})), Br = /* @__PURE__ */ p(((e) => {
	var t = _();
	function n(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var r = typeof Object.is == "function" ? Object.is : n, i = t.useState, a = t.useEffect, o = t.useLayoutEffect, s = t.useDebugValue;
	function c(e, t) {
		var n = t(), r = i({ inst: {
			value: n,
			getSnapshot: t
		} }), c = r[0].inst, u = r[1];
		return o(function() {
			c.value = n, c.getSnapshot = t, l(c) && u({ inst: c });
		}, [
			e,
			n,
			t
		]), a(function() {
			return l(c) && u({ inst: c }), e(function() {
				l(c) && u({ inst: c });
			});
		}, [e]), s(n), n;
	}
	function l(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !r(e, n);
		} catch {
			return !0;
		}
	}
	function u(e, t) {
		return t();
	}
	var d = typeof window > "u" || window.document === void 0 || window.document.createElement === void 0 ? u : c;
	e.useSyncExternalStore = t.useSyncExternalStore === void 0 ? d : t.useSyncExternalStore;
})), Vr = /* @__PURE__ */ p(((e, t) => {
	t.exports = Br();
})), Hr = /* @__PURE__ */ h(zr(), 1), Ur = Vr(), Wr = /*#__PURE__*/ (0, b.createContext)(!1), Gr = /*#__PURE__*/ (0, b.createContext)(null);
function Kr(e) {
	if ((0, b.useContext)(Gr)) return e.content;
	let { collection: t, document: n } = Xr(e.createCollection);
	return /*#__PURE__*/ b.createElement(b.Fragment, null, /*#__PURE__*/ b.createElement(Fr, null, /*#__PURE__*/ b.createElement(Gr.Provider, { value: n }, e.content)), /*#__PURE__*/ b.createElement(qr, {
		render: e.children,
		collection: t
	}));
}
function qr({ collection: e, render: t }) {
	return t(e);
}
function Jr(e, t, n) {
	let r = En(), i = (0, b.useRef)(r);
	i.current = r;
	let a = (0, b.useCallback)(() => i.current ? n() : t(), [t, n]);
	return (0, Ur.useSyncExternalStore)(e, a);
}
var Yr = typeof b.useSyncExternalStore == "function" ? b.useSyncExternalStore : Jr;
function Xr(e) {
	let [t] = (0, b.useState)(() => new mt(e?.() || new ut()));
	return {
		collection: Yr((0, b.useCallback)((e) => t.subscribe(e), [t]), (0, b.useCallback)(() => {
			let e = t.getCollection();
			return t.isSSR && t.resetAfterSSR(), e;
		}, [t]), (0, b.useCallback)(() => (t.isSSR = !0, t.getCollection()), [t])),
		document: t
	};
}
var Zr = /*#__PURE__*/ (0, b.createContext)(null);
function Qr(e) {
	return class extends ot {
		static {
			this.type = e;
		}
	};
}
function $r(e, t, n, r, i, a) {
	typeof e == "string" && (e = Qr(e));
	let o = (0, b.useCallback)((i) => {
		i?.setProps(t, n, e, r, a);
	}, [
		t,
		n,
		r,
		a,
		e
	]), s = (0, b.useContext)(Zr);
	if (s) {
		let o = s.ownerDocument.nodesByProps.get(t);
		return o || (o = s.ownerDocument.createElement(e.type), o.setProps(t, n, e, r, a), s.appendChild(o), s.ownerDocument.updateCollection(), s.ownerDocument.nodesByProps.set(t, o)), i ? /*#__PURE__*/ b.createElement(Zr.Provider, { value: o }, i) : null;
	}
	return /*#__PURE__*/ b.createElement(e.type, { ref: o }, i);
}
function ei(e, t) {
	let n = ({ node: e }) => t(e.props, e.props.ref, e), r = (0, b.forwardRef)((r, i) => {
		let a = (0, b.useContext)(jr);
		if (!(0, b.useContext)(Wr)) {
			if (t.length >= 3) throw Error(t.name + " cannot be rendered outside a collection.");
			return t(r, i);
		}
		return $r(e, r, i, "children" in r ? r.children : null, null, (e) => /*#__PURE__*/ b.createElement(jr.Provider, { value: a }, /*#__PURE__*/ b.createElement(n, { node: e })));
	});
	return r.displayName = t.name, r;
}
function ti(e) {
	return ht({
		...e,
		addIdAndValue: !0
	});
}
var ni = /*#__PURE__*/ (0, b.createContext)(null);
function ri(e) {
	let t = (0, b.useContext)(ni), n = (t?.dependencies || []).concat(e.dependencies), r = e.idScope ?? t?.idScope, i = ti({
		...e,
		idScope: r,
		dependencies: n
	});
	return (0, b.useContext)(Gr) && (i = /*#__PURE__*/ b.createElement(ii, null, i)), t = (0, b.useMemo)(() => ({
		dependencies: n,
		idScope: r
	}), [r, ...n]), /*#__PURE__*/ b.createElement(ni.Provider, { value: t }, i);
}
function ii({ children: e }) {
	let t = (0, b.useContext)(Gr), n = (0, b.useMemo)(() => /*#__PURE__*/ b.createElement(Gr.Provider, { value: null }, /*#__PURE__*/ b.createElement(Wr.Provider, { value: !0 }, e)), [e]);
	return En() ? /*#__PURE__*/ b.createElement(Zr.Provider, { value: t }, n) : /*#__PURE__*/ (0, Hr.createPortal)(n, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/constants.mjs
var ai = "react-aria-clear-focus", oi = "react-aria-focus";
//#endregion
//#region node_modules/react-aria/dist/private/focus/virtualFocus.mjs
function si(e) {
	let t = ui(R(e));
	t !== e && (t && ci(t, e), e && li(e, t));
}
function ci(e, t) {
	e.dispatchEvent(new FocusEvent("blur", { relatedTarget: t })), e.dispatchEvent(new FocusEvent("focusout", {
		bubbles: !0,
		relatedTarget: t
	}));
}
function li(e, t) {
	e.dispatchEvent(new FocusEvent("focus", { relatedTarget: t })), e.dispatchEvent(new FocusEvent("focusin", {
		bubbles: !0,
		relatedTarget: t
	}));
}
function ui(e) {
	let t = jt(e), n = t?.getAttribute("aria-activedescendant");
	return n && e.getElementById(n) || t;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/keyboard.mjs
function di(e) {
	return Zt() ? e.metaKey : e.ctrlKey;
}
var fi = /* @__PURE__ */ new Set([
	"checkbox",
	"radio",
	"range",
	"color",
	"file",
	"image",
	"button",
	"submit",
	"reset"
]);
function pi(e) {
	return e instanceof HTMLInputElement && !fi.has(e.type) || e instanceof HTMLTextAreaElement || e instanceof HTMLElement && e.isContentEditable;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useEffectEvent.mjs
var mi = b.useInsertionEffect ?? H;
function hi(e) {
	let t = (0, b.useRef)(null);
	return mi(() => {
		t.current = e;
	}, [e]), (0, b.useCallback)((...e) => {
		let n = t.current;
		return n?.(...e);
	}, []);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useEvent.mjs
function gi(e, t, n, r) {
	let i = hi(n), a = n == null;
	(0, b.useEffect)(() => {
		if (!(a || e.current == null)) return Dt(e.current, t, i, r);
	}, [
		e,
		t,
		r,
		a
	]);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useLabels.mjs
function _i(e, t) {
	let { id: n, "aria-label": r, "aria-labelledby": i } = e;
	return n = sr(n), i && r ? i = [.../* @__PURE__ */ new Set([n, ...i.trim().split(/\s+/)])].join(" ") : i &&= i.trim().split(/\s+/).join(" "), !r && !i && t && (r = t), {
		id: n,
		"aria-label": r,
		"aria-labelledby": i
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/utils.mjs
var vi = /* @__PURE__ */ new Set([
	"Arab",
	"Syrc",
	"Samr",
	"Mand",
	"Thaa",
	"Mend",
	"Nkoo",
	"Adlm",
	"Rohg",
	"Hebr"
]), yi = /* @__PURE__ */ new Set([
	"ae",
	"ar",
	"arc",
	"bcc",
	"bqi",
	"ckb",
	"dv",
	"fa",
	"glk",
	"he",
	"ku",
	"mzn",
	"nqo",
	"pnb",
	"ps",
	"sd",
	"ug",
	"ur",
	"yi"
]);
function bi(e) {
	if (Intl.Locale) {
		let t = new Intl.Locale(e).maximize(), n = typeof t.getTextInfo == "function" ? t.getTextInfo() : t.textInfo;
		if (n) return n.direction === "rtl";
		if (t.script) return vi.has(t.script);
	}
	let t = e.split("-")[0];
	return yi.has(t);
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/useDefaultLocale.mjs
var xi = Symbol.for("react-aria.i18n.locale");
function Si() {
	let e = typeof window < "u" && window[xi] || typeof navigator < "u" && (navigator.language || navigator.userLanguage) || "en-US";
	try {
		Intl.DateTimeFormat.supportedLocalesOf([e]);
	} catch {
		e = "en-US";
	}
	return {
		locale: e,
		direction: bi(e) ? "rtl" : "ltr"
	};
}
var Ci = Si(), wi = /* @__PURE__ */ new Set();
function Ti() {
	Ci = Si();
	for (let e of wi) e(Ci);
}
function Ei() {
	let e = En(), [t, n] = (0, b.useState)(Ci);
	return (0, b.useEffect)(() => (wi.size === 0 && window.addEventListener("languagechange", Ti), wi.add(n), () => {
		wi.delete(n), wi.size === 0 && window.removeEventListener("languagechange", Ti);
	}), []), e ? {
		locale: typeof window < "u" && window[xi] || "en-US",
		direction: "ltr"
	} : t;
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/I18nProvider.mjs
var Di = /*#__PURE__*/ b.createContext(null);
function Oi() {
	let e = Ei();
	return (0, b.useContext)(Di) || e;
}
//#endregion
//#region node_modules/@internationalized/string/dist/private/LocalizedStringDictionary.mjs
var ki = Symbol.for("react-aria.i18n.locale"), Ai = Symbol.for("react-aria.i18n.strings"), ji = void 0, Mi = class e {
	constructor(e, t = "en-US") {
		this.strings = Object.fromEntries(Object.entries(e).filter(([, e]) => e)), this.defaultLocale = t;
	}
	getStringForLocale(e, t) {
		let n = this.getStringsForLocale(t)[e];
		if (!n) throw Error(`Could not find intl message ${e} in ${t} locale`);
		return n;
	}
	getStringsForLocale(e) {
		let t = this.strings[e];
		return t || (t = Ni(e, this.strings, this.defaultLocale), this.strings[e] = t), t;
	}
	static getGlobalDictionaryForPackage(t) {
		if (typeof window > "u") return null;
		let n = window[ki];
		if (ji === void 0) {
			let t = window[Ai];
			if (!t) return null;
			ji = {};
			for (let r in t) ji[r] = new e({ [n]: t[r] }, n);
		}
		let r = ji?.[t];
		if (!r) throw Error(`Strings for package "${t}" were not included by LocalizedStringProvider. Please add it to the list passed to createLocalizedStringDictionary.`);
		return r;
	}
};
function Ni(e, t, n = "en-US") {
	if (t[e]) return t[e];
	let r = Pi(e), i = Fi(e);
	if (i && t[`${r}-${i}`]) return t[`${r}-${i}`];
	if (t[r]) return t[r];
	for (let e in t) if (e.startsWith(r + "-")) return t[e];
	return t[n];
}
function Pi(e) {
	return Intl.Locale ? new Intl.Locale(e).language : e.split("-")[0];
}
function Fi(e) {
	if (Intl.Locale) return new Intl.Locale(e).script;
}
//#endregion
//#region node_modules/@internationalized/string/dist/private/LocalizedStringFormatter.mjs
var Ii = /* @__PURE__ */ new Map(), Li = /* @__PURE__ */ new Map(), Ri = class {
	constructor(e, t) {
		this.locale = e, this.strings = t;
	}
	format(e, t) {
		let n = this.strings.getStringForLocale(e, this.locale);
		return typeof n == "function" ? n(t, this) : n;
	}
	plural(e, t, n = "cardinal") {
		let r = t["=" + e];
		if (r) return typeof r == "function" ? r() : r;
		let i = this.locale + ":" + n, a = Ii.get(i);
		return a || (a = new Intl.PluralRules(this.locale, { type: n }), Ii.set(i, a)), r = t[a.select(e)] || t.other, typeof r == "function" ? r() : r;
	}
	number(e) {
		let t = Li.get(this.locale);
		return t || (t = new Intl.NumberFormat(this.locale), Li.set(this.locale, t)), t.format(e);
	}
	select(e, t) {
		let n = e[t] || e.other;
		return typeof n == "function" ? n() : n;
	}
}, zi = /* @__PURE__ */ new WeakMap();
function Bi(e) {
	let t = zi.get(e);
	return t || (t = new Mi(e), zi.set(e, t)), t;
}
function Vi(e, t) {
	return t && Mi.getGlobalDictionaryForPackage(t) || Bi(e);
}
function Hi(e, t) {
	let { locale: n } = Oi(), r = Vi(e, t);
	return (0, b.useMemo)(() => new Ri(n, r), [n, r]);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/filterDOMProps.mjs
var Ui = /* @__PURE__ */ new Set(["id"]), Wi = /* @__PURE__ */ new Set([
	"aria-label",
	"aria-labelledby",
	"aria-describedby",
	"aria-details"
]), Gi = /* @__PURE__ */ new Set([
	"href",
	"hrefLang",
	"target",
	"rel",
	"download",
	"ping",
	"referrerPolicy"
]), Ki = /* @__PURE__ */ new Set([
	"dir",
	"lang",
	"hidden",
	"inert",
	"translate"
]), qi = /* @__PURE__ */ new Set(/* @__PURE__ */ "onClick.onAuxClick.onContextMenu.onDoubleClick.onMouseDown.onMouseEnter.onMouseLeave.onMouseMove.onMouseOut.onMouseOver.onMouseUp.onTouchCancel.onTouchEnd.onTouchMove.onTouchStart.onPointerDown.onPointerMove.onPointerUp.onPointerCancel.onPointerEnter.onPointerLeave.onPointerOver.onPointerOut.onGotPointerCapture.onLostPointerCapture.onScroll.onWheel.onAnimationStart.onAnimationEnd.onAnimationIteration.onTransitionCancel.onTransitionEnd.onTransitionRun.onTransitionStart".split(".")), Ji = /^(data-.*)$/;
function Yi(e, t = {}) {
	let { labelable: n, isLink: r, global: i, events: a = i, propNames: o } = t, s = {};
	for (let t in e) Object.prototype.hasOwnProperty.call(e, t) && (Ui.has(t) || n && Wi.has(t) || r && Gi.has(t) || i && Ki.has(t) || a && (qi.has(t) || t.endsWith("Capture") && qi.has(t.slice(0, -7))) || o?.has(t) || Ji.test(t)) && (s[t] = e[t]);
	return s;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/textSelection.mjs
var Xi = "default", Zi = "", Qi = /* @__PURE__ */ new WeakMap();
function $i(e) {
	if (en() && nn()) {
		if (Xi === "default") {
			let t = R(e);
			Zi = t.documentElement.style.webkitUserSelect, t.documentElement.style.webkitUserSelect = "none";
		}
		Xi = "disabled";
	} else if (e instanceof HTMLElement || e instanceof SVGElement) {
		let t = "userSelect" in e.style ? "userSelect" : "webkitUserSelect";
		Qi.set(e, e.style[t]), e.style[t] = "none";
	}
}
function W(e) {
	if (en() && nn()) {
		if (Xi !== "disabled") return;
		Xi = "restoring", setTimeout(() => {
			$n(() => {
				if (Xi === "restoring") {
					let t = R(e);
					t.documentElement.style.webkitUserSelect === "none" && (t.documentElement.style.webkitUserSelect = Zi || ""), Zi = "", Xi = "default";
				}
			});
		}, 300);
	} else if ((e instanceof HTMLElement || e instanceof SVGElement) && e && Qi.has(e)) {
		let t = Qi.get(e), n = "userSelect" in e.style ? "userSelect" : "webkitUserSelect";
		e.style[n] === "none" && (e.style[n] = t), e.getAttribute("style") === "" && e.removeAttribute("style"), Qi.delete(e);
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getMetaValue.mjs
function ea(e, t) {
	let n = St(t), r = R(t);
	if (r == null || n == null) return;
	let i, a = `meta[name="${CSS.escape(e)}"], meta[property="${CSS.escape(e)}"]`, o = r.querySelector(a);
	return o && o instanceof n.HTMLMetaElement && (e === "csp-nonce" && o.nonce && (i ??= o.nonce || void 0), o.content && (i ??= o.content || void 0)), e === "csp-nonce" && (i ??= n.__webpack_nonce__ || globalThis.__webpack_nonce__ || void 0), i;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getNonce.mjs
var ta = /* @__PURE__ */ new WeakMap();
function na(e) {
	let t = R(e), n = ta.get(t);
	return n ??= ea("csp-nonce", t), n !== void 0 && ta.set(t, n), n;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/context.mjs
var ra = b.createContext({ register: () => {} });
ra.displayName = "PressResponderContext";
//#endregion
//#region node_modules/react-aria/dist/private/utils/useGlobalListeners.mjs
function ia() {
	let e = (0, b.useRef)(/* @__PURE__ */ new Map()), t = (0, b.useCallback)((t, n, r, i) => {
		let a = i?.once ? (...t) => {
			e.current.delete(r), r(...t);
		} : r;
		e.current.set(r, {
			type: n,
			eventTarget: t,
			fn: a,
			options: i
		}), t.addEventListener(n, a, i);
	}, []), n = (0, b.useCallback)((t, n, r, i) => {
		let a = e.current.get(r)?.fn || r;
		t.removeEventListener(n, a, i), e.current.delete(r);
	}, []), r = (0, b.useCallback)(() => {
		e.current.forEach((e, t) => {
			n(e.eventTarget, e.type, t, e.options);
		});
	}, [n]);
	return (0, b.useEffect)(() => r, [r]), {
		addGlobalListener: t,
		removeGlobalListener: n,
		removeAllGlobalListeners: r
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/usePress.mjs
function aa(e) {
	let t = (0, b.useContext)(ra);
	if (t) {
		let { register: n, ref: r, ...i } = t;
		e = U(i, e), n();
	}
	return Ar(t, e.ref), e;
}
var oa = class {
	#e;
	constructor(e, t, n, r) {
		this.#e = !0;
		let i = (r?.target ?? n.currentTarget)?.getBoundingClientRect(), a, o = 0, s, c = null;
		n.clientX != null && n.clientY != null && (s = n.clientX, c = n.clientY), i && (s != null && c != null ? (a = s - i.left, o = c - i.top) : (a = i.width / 2, o = i.height / 2)), this.type = e, this.pointerType = t, this.target = n.currentTarget, this.shiftKey = n.shiftKey, this.metaKey = n.metaKey, this.ctrlKey = n.ctrlKey, this.altKey = n.altKey, this.x = a, this.y = o, this.key = n.key;
	}
	continuePropagation() {
		this.#e = !1;
	}
	get shouldStopPropagation() {
		return this.#e;
	}
}, sa = Symbol("linkClicked"), ca = "react-aria-pressable-style", la = "data-react-aria-pressable";
function ua(e) {
	let { onPress: t, onPressChange: n, onPressStart: r, onPressEnd: i, onPressUp: a, onClick: o, isDisabled: s, isPressed: c, preventFocusOnPress: l, shouldCancelOnPointerExit: u, allowTextSelectionOnPress: d, ref: f, ...p } = aa(e), [m, h] = (0, b.useState)(!1), g = (0, b.useRef)({
		isPressed: !1,
		ignoreEmulatedMouseEvents: !1,
		didFirePressStart: !1,
		isTriggeringEvent: !1,
		activePointerId: null,
		target: null,
		isOverTarget: !1,
		pointerType: null,
		disposables: []
	}), { addGlobalListener: _, removeAllGlobalListeners: v } = ia(), y = (0, b.useCallback)((e, t) => {
		let i = g.current;
		if (s || i.didFirePressStart) return !1;
		let a = !0;
		if (i.isTriggeringEvent = !0, r) {
			let n = new oa("pressstart", t, e);
			r(n), a = n.shouldStopPropagation;
		}
		return n && n(!0), i.isTriggeringEvent = !1, i.didFirePressStart = !0, h(!0), a;
	}, [
		s,
		r,
		n
	]), x = (0, b.useCallback)((e, r, a = !0) => {
		let o = g.current;
		if (!o.didFirePressStart) return !1;
		o.didFirePressStart = !1, o.isTriggeringEvent = !0;
		let c = !0;
		if (i) {
			let t = new oa("pressend", r, e);
			i(t), c = t.shouldStopPropagation;
		}
		if (n && n(!1), h(!1), t && a && !s) {
			let n = new oa("press", r, e);
			t(n), c &&= n.shouldStopPropagation;
		}
		return o.isTriggeringEvent = !1, c;
	}, [
		s,
		i,
		n,
		t
	]), S = hi(x), C = hi((0, b.useCallback)((e, t) => {
		let n = g.current;
		if (s) return !1;
		if (a) {
			n.isTriggeringEvent = !0;
			let r = new oa("pressup", t, e);
			return a(r), n.isTriggeringEvent = !1, r.shouldStopPropagation;
		}
		return !0;
	}, [s, a])), w = (0, b.useCallback)((e) => {
		let t = g.current;
		if (t.isPressed && t.target) {
			t.didFirePressStart && t.pointerType != null && x(pa(t.target, e), t.pointerType, !1), t.isPressed = !1, t.isOverTarget = !1, t.activePointerId = null, t.pointerType = null, v(), d || W(t.target);
			for (let e of t.disposables) e();
			t.disposables = [];
		}
	}, [
		d,
		v,
		x
	]), T = hi(w);
	(0, b.useEffect)(() => {
		s && g.current.isPressed && T({
			currentTarget: g.current.target,
			shiftKey: !1,
			ctrlKey: !1,
			metaKey: !1,
			altKey: !1
		});
	}, [s]);
	let E = (0, b.useCallback)((e) => {
		u && w(e);
	}, [u, w]), D = (0, b.useCallback)((e) => {
		s || o?.(e);
	}, [s, o]), O = (0, b.useCallback)((e, t) => {
		if (!s && o) {
			let n = new MouseEvent("click", e);
			Wt(n, t), o(Ut(n));
		}
	}, [s, o]), k = (0, b.useMemo)(() => {
		let e = g.current, t = {
			onKeyDown(t) {
				if (fa(t.nativeEvent, t.currentTarget) && z(t.currentTarget, B(t))) {
					ha(B(t), t.key) && t.preventDefault();
					let r = !0;
					!e.isPressed && !t.repeat && (e.target = t.currentTarget, e.isPressed = !0, e.pointerType = "keyboard", r = y(t, "keyboard"));
					let i = t.currentTarget;
					_(R(t.currentTarget), "keyup", tr((t) => {
						fa(t, i) && !t.repeat && z(i, B(t)) && e.target && C(pa(e.target, t), "keyboard");
					}, n), !0), r && t.stopPropagation(), t.metaKey && Zt() && e.metaKeyEvents?.set(t.key, t.nativeEvent);
				} else t.key === "Meta" && (e.metaKeyEvents = /* @__PURE__ */ new Map());
			},
			onClick(t) {
				if (!(t && !z(t.currentTarget, B(t))) && t && t.button === 0 && !e.isTriggeringEvent && !dn.isOpening) {
					let n = !0;
					if (s && t.preventDefault(), !e.ignoreEmulatedMouseEvents && !e.isPressed && (e.pointerType === "virtual" || sn(t.nativeEvent))) {
						let e = y(t, "virtual"), r = C(t, "virtual"), i = S(t, "virtual");
						D(t), n = e && r && i;
					} else if (e.isPressed && e.pointerType !== "keyboard") {
						let r = e.pointerType || t.nativeEvent.pointerType || "virtual", i = C(pa(t.currentTarget, t), r), a = S(pa(t.currentTarget, t), r, !0);
						n = i && a, e.isOverTarget = !1, D(t), T(t);
					}
					e.ignoreEmulatedMouseEvents = !1, n && t.stopPropagation();
				}
			}
		}, n = (t) => {
			if (e.isPressed && e.target && fa(t, e.target)) {
				ha(B(t), t.key) && t.preventDefault();
				let n = B(t), r = z(e.target, n);
				S(pa(e.target, t), "keyboard", r), r && O(t, e.target), v(), t.key !== "Enter" && da(e.target) && z(e.target, n) && !t[sa] && (t[sa] = !0, dn(e.target, t, !1)), e.isPressed = !1, e.metaKeyEvents?.delete(t.key);
			} else if (t.key === "Meta" && e.metaKeyEvents?.size) {
				let t = e.metaKeyEvents;
				e.metaKeyEvents = void 0;
				for (let n of t.values()) e.target?.dispatchEvent(new KeyboardEvent("keyup", n));
			}
		};
		if (typeof PointerEvent < "u") {
			t.onPointerDown = (t) => {
				if (t.button !== 0 || !z(t.currentTarget, B(t))) return;
				if (cn(t.nativeEvent)) {
					e.pointerType = "virtual";
					return;
				}
				e.pointerType = t.pointerType;
				let i = !0;
				if (!e.isPressed) {
					e.isPressed = !0, e.isOverTarget = !0, e.activePointerId = t.pointerId, e.target = t.currentTarget, d || $i(e.target), i = y(t, e.pointerType);
					let a = B(t);
					"releasePointerCapture" in a && ("hasPointerCapture" in a ? a.hasPointerCapture(t.pointerId) && a.releasePointerCapture(t.pointerId) : a.releasePointerCapture(t.pointerId)), _(R(t.currentTarget), "pointerup", n, !1), _(R(t.currentTarget), "pointercancel", r, !1);
				}
				i && t.stopPropagation();
			}, t.onMouseDown = (t) => {
				if (z(t.currentTarget, B(t)) && t.button === 0) {
					if (l) {
						let n = qt(t.target);
						n && e.disposables.push(n);
					}
					t.stopPropagation();
				}
			}, t.onPointerUp = (t) => {
				!z(t.currentTarget, B(t)) || e.pointerType === "virtual" || t.button === 0 && !e.isPressed && C(t, e.pointerType || t.pointerType);
			}, t.onPointerEnter = (t) => {
				t.pointerId === e.activePointerId && e.target && !e.isOverTarget && e.pointerType != null && (e.isOverTarget = !0, y(pa(e.target, t), e.pointerType));
			}, t.onPointerLeave = (t) => {
				t.pointerId === e.activePointerId && e.target && e.isOverTarget && e.pointerType != null && (e.isOverTarget = !1, S(pa(e.target, t), e.pointerType, !1), E(t));
			};
			let n = (t) => {
				if (t.pointerId === e.activePointerId && e.isPressed && t.button === 0 && e.target) {
					if (z(e.target, B(t)) && e.pointerType != null) {
						let n = !1, r = setTimeout(() => {
							e.isPressed && e.target instanceof HTMLElement && (n ? T(t) : (_t(e.target), e.target.click()));
						}, 80);
						_(t.currentTarget, "click", () => n = !0, !0), e.disposables.push(() => clearTimeout(r));
					} else T(t);
					e.isOverTarget = !1;
				}
			}, r = (e) => {
				T(e);
			};
			t.onDragStart = (e) => {
				z(e.currentTarget, B(e)) && T(e);
			};
		}
		return t;
	}, [
		_,
		s,
		l,
		v,
		d,
		E,
		y,
		D,
		O
	]);
	return (0, b.useEffect)(() => {
		if (!f) return;
		let e = R(f.current);
		if (!e || !e.head || e.getElementById(ca)) return;
		let t = e.createElement("style");
		t.id = ca;
		let n = na(e);
		n && (t.nonce = n), t.textContent = `
@layer {
  [${la}] {
    touch-action: pan-x pan-y pinch-zoom;
  }
}
    `.trim(), e.head.prepend(t);
	}, [f]), (0, b.useEffect)(() => {
		let e = g.current;
		return () => {
			d || W(e.target ?? void 0);
			for (let t of e.disposables) t();
			e.disposables = [];
		};
	}, [d]), {
		isPressed: c || m,
		pressProps: U(p, k, { [la]: !0 })
	};
}
function da(e) {
	return e.tagName === "A" && e.hasAttribute("href");
}
function fa(e, t) {
	let { key: n, code: r } = e, i = t, a = i.getAttribute("role");
	return (n === "Enter" || n === " " || n === "Spacebar" || r === "Space") && !(i instanceof St(i).HTMLInputElement && !_a(i, n) || i instanceof St(i).HTMLTextAreaElement || i.isContentEditable) && !((a === "link" || !a && da(i)) && n !== "Enter");
}
function pa(e, t) {
	let n = t.clientX, r = t.clientY;
	return {
		currentTarget: e,
		shiftKey: t.shiftKey,
		ctrlKey: t.ctrlKey,
		metaKey: t.metaKey,
		altKey: t.altKey,
		clientX: n,
		clientY: r,
		key: t.key
	};
}
function ma(e) {
	return e instanceof HTMLInputElement ? !1 : e instanceof HTMLButtonElement ? e.type !== "submit" && e.type !== "reset" : !da(e);
}
function ha(e, t) {
	return Zt() && t === "Enter" ? !1 : e instanceof HTMLInputElement ? t === "Enter" && (e.type === "checkbox" || e.type === "radio") ? !1 : !_a(e, t) : ma(e);
}
var ga = /* @__PURE__ */ new Set([
	"checkbox",
	"radio",
	"range",
	"color",
	"file",
	"image",
	"button",
	"submit",
	"reset"
]);
function _a(e, t) {
	return e.type === "checkbox" || e.type === "radio" ? t === " " : ga.has(e.type);
}
//#endregion
//#region node_modules/react-aria/dist/private/button/useButton.mjs
function va(e, t) {
	let { elementType: n = "button", isDisabled: r, onPress: i, onPressStart: a, onPressEnd: o, onPressUp: s, onPressChange: c, preventFocusOnPress: l, allowFocusWhenDisabled: u, onClick: d, href: f, target: p, rel: m, type: h = "button" } = e, g;
	g = n === "button" ? {
		type: h,
		disabled: r,
		form: e.form,
		formAction: e.formAction,
		formEncType: e.formEncType,
		formMethod: e.formMethod,
		formNoValidate: e.formNoValidate,
		formTarget: e.formTarget,
		name: e.name,
		value: e.value
	} : {
		role: "button",
		href: n === "a" && !r ? f : void 0,
		target: n === "a" ? p : void 0,
		type: n === "input" ? h : void 0,
		disabled: n === "input" ? r : void 0,
		"aria-disabled": !r || n === "input" ? void 0 : r,
		rel: n === "a" ? m : void 0
	};
	let { pressProps: _, isPressed: v } = ua({
		onPressStart: a,
		onPressEnd: o,
		onPressChange: c,
		onPress: i,
		onPressUp: s,
		onClick: d,
		isDisabled: r,
		preventFocusOnPress: l,
		ref: t
	}), { focusableProps: y } = Nr(e, t);
	u && (y.tabIndex = r ? -1 : y.tabIndex);
	let b = U(y, _, Yi(e, { labelable: !0 }));
	return {
		isPressed: v,
		buttonProps: U(g, b, {
			"aria-haspopup": e["aria-haspopup"],
			"aria-expanded": e["aria-expanded"],
			"aria-controls": e["aria-controls"],
			"aria-pressed": e["aria-pressed"],
			"aria-current": e["aria-current"],
			"aria-disabled": e["aria-disabled"]
		})
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/shadowdom/ShadowTreeWalker.mjs
var ya = class {
	constructor(e, t, n, r) {
		this._walkerStack = [], this._currentSetFor = /* @__PURE__ */ new Set(), this._acceptNode = (e) => {
			if (e.nodeType === Node.ELEMENT_NODE) {
				let t = e.shadowRoot;
				if (t) {
					let e = this._doc.createTreeWalker(t, this.whatToShow, { acceptNode: this._acceptNode });
					return this._walkerStack.unshift(e), NodeFilter.FILTER_ACCEPT;
				}
				if (typeof this.filter == "function") return this.filter(e);
				if (this.filter?.acceptNode) return this.filter.acceptNode(e);
				if (this.filter === null) return NodeFilter.FILTER_ACCEPT;
			}
			return NodeFilter.FILTER_SKIP;
		}, this._doc = e, this.root = t, this.filter = r ?? null, this.whatToShow = n ?? NodeFilter.SHOW_ALL, this._currentNode = t, this._walkerStack.unshift(e.createTreeWalker(t, n, this._acceptNode));
		let i = t.shadowRoot;
		if (i) {
			let e = this._doc.createTreeWalker(i, this.whatToShow, { acceptNode: this._acceptNode });
			this._walkerStack.unshift(e);
		}
	}
	get currentNode() {
		return this._currentNode;
	}
	set currentNode(e) {
		if (!z(this.root, e)) throw Error("Cannot set currentNode to a node that is not contained by the root node.");
		let t = [], n = e, r = e;
		for (this._currentNode = e; n && n !== this.root;) if (n.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
			let e = n, i = this._doc.createTreeWalker(e, this.whatToShow, { acceptNode: this._acceptNode });
			t.push(i), i.currentNode = r, this._currentSetFor.add(i), n = r = e.host;
		} else n = n.parentNode;
		let i = this._doc.createTreeWalker(this.root, this.whatToShow, { acceptNode: this._acceptNode });
		t.push(i), i.currentNode = r, this._currentSetFor.add(i), this._walkerStack = t;
	}
	get doc() {
		return this._doc;
	}
	firstChild() {
		let e = this.currentNode, t = this.nextNode();
		return z(e, t) ? (t && (this.currentNode = t), t) : (this.currentNode = e, null);
	}
	lastChild() {
		let e = this._walkerStack[0].lastChild();
		return e && (this.currentNode = e), e;
	}
	nextNode() {
		let e = this._walkerStack[0].nextNode();
		if (e) {
			if (e.shadowRoot) {
				let t;
				if (typeof this.filter == "function" ? t = this.filter(e) : this.filter?.acceptNode && (t = this.filter.acceptNode(e)), t === NodeFilter.FILTER_ACCEPT) return this.currentNode = e, e;
				let n = this.nextNode();
				return n && (this.currentNode = n), n;
			}
			return e && (this.currentNode = e), e;
		}
		if (this._walkerStack.length > 1) {
			this._walkerStack.shift();
			let e = this.nextNode();
			return e && (this.currentNode = e), e;
		}
		return null;
	}
	previousNode() {
		let e = this._walkerStack[0];
		if (e.currentNode === e.root) {
			if (this._currentSetFor.has(e)) {
				if (this._currentSetFor.delete(e), this._walkerStack.length > 1) {
					this._walkerStack.shift();
					let e = this.previousNode();
					return e && (this.currentNode = e), e;
				}
				return null;
			}
			return null;
		}
		let t = e.previousNode();
		if (t) {
			if (t.shadowRoot) {
				let e;
				if (typeof this.filter == "function" ? e = this.filter(t) : this.filter?.acceptNode && (e = this.filter.acceptNode(t)), e === NodeFilter.FILTER_ACCEPT) return t && (this.currentNode = t), t;
				let n = this.lastChild();
				return n && (this.currentNode = n), n;
			}
			return t && (this.currentNode = t), t;
		}
		if (this._walkerStack.length > 1) {
			this._walkerStack.shift();
			let e = this.previousNode();
			return e && (this.currentNode = e), e;
		}
		return null;
	}
	nextSibling() {
		return null;
	}
	previousSibling() {
		return null;
	}
	parentNode() {
		return null;
	}
};
function ba(e, t, n, r) {
	return At() ? new ya(e, t, n, r) : e.createTreeWalker(t, n, r);
}
//#endregion
//#region node_modules/react-aria/dist/private/focus/FocusScope.mjs
var xa = /*#__PURE__*/ b.createContext(null), Sa = "react-aria-focus-scope-restore", Ca = null;
function wa(e) {
	let { children: t, contain: n, restoreFocus: r, autoFocus: i } = e, a = (0, b.useRef)(null), o = (0, b.useRef)(null), s = (0, b.useRef)([]), { parentNode: c } = (0, b.useContext)(xa) || {}, l = (0, b.useMemo)(() => new Ka({ scopeRef: s }), [s]);
	H(() => {
		let e = c || qa.root;
		if (qa.getTreeNode(e.scopeRef) && Ca && !Fa(Ca, e.scopeRef)) {
			let t = qa.getTreeNode(Ca);
			t && (e = t);
		}
		e.addChild(l), qa.addNode(l);
	}, [l, c]), H(() => {
		let e = qa.getTreeNode(s);
		e && (e.contain = !!n);
	}, [n]), H(() => {
		let e = a.current?.nextSibling, t = [], n = (e) => e.stopPropagation();
		for (; e && e !== o.current;) t.push(e), e.addEventListener(Sa, n), e = e.nextSibling;
		return s.current = t, () => {
			for (let e of t) e.removeEventListener(Sa, n);
		};
	}, [t]), Ba(s, r, n), Aa(s, n), Ha(s, r, n), za(s, i), (0, b.useEffect)(() => {
		let e = jt(R(s.current ? s.current[0] : void 0)), t = null;
		if (Ma(e, s.current)) {
			for (let n of qa.traverse()) n.scopeRef && Ma(e, n.scopeRef.current) && (t = n);
			t === qa.getTreeNode(s) && (Ca = t.scopeRef);
		}
	}, [s]), H(() => () => {
		let e = qa.getTreeNode(s)?.parent?.scopeRef ?? null;
		(s === Ca || Fa(s, Ca)) && (!e || qa.getTreeNode(e)) && (Ca = e), qa.removeTreeNode(s);
	}, [s]);
	let u = (0, b.useMemo)(() => Ta(s), []), d = (0, b.useMemo)(() => ({
		focusManager: u,
		parentNode: l
	}), [l, u]);
	return /*#__PURE__*/ b.createElement(xa.Provider, { value: d }, /*#__PURE__*/ b.createElement("span", {
		"data-focus-scope-start": !0,
		hidden: !0,
		ref: a
	}), t, /*#__PURE__*/ b.createElement("span", {
		"data-focus-scope-end": !0,
		hidden: !0,
		ref: o
	}));
}
function Ta(e) {
	return {
		focusNext(t = {}) {
			let n = e.current, { from: r, tabbable: i, wrap: a, accept: o } = t, s = r || jt(R(n[0] ?? void 0)), c = n[0].previousElementSibling, l = Wa(Ea(n), {
				tabbable: i,
				accept: o
			}, n);
			l.currentNode = Ma(s, n) ? s : c;
			let u = l.nextNode();
			return !u && a && (l.currentNode = c, u = l.nextNode()), u && Ia(u, !0), u;
		},
		focusPrevious(t = {}) {
			let n = e.current, { from: r, tabbable: i, wrap: a, accept: o } = t, s = r || jt(R(n[0] ?? void 0)), c = n[n.length - 1].nextElementSibling, l = Wa(Ea(n), {
				tabbable: i,
				accept: o
			}, n);
			l.currentNode = Ma(s, n) ? s : c;
			let u = l.previousNode();
			return !u && a && (l.currentNode = c, u = l.previousNode()), u && Ia(u, !0), u;
		},
		focusFirst(t = {}) {
			let n = e.current, { tabbable: r, accept: i } = t, a = Wa(Ea(n), {
				tabbable: r,
				accept: i
			}, n);
			a.currentNode = n[0].previousElementSibling;
			let o = a.nextNode();
			return o && Ia(o, !0), o;
		},
		focusLast(t = {}) {
			let n = e.current, { tabbable: r, accept: i } = t, a = Wa(Ea(n), {
				tabbable: r,
				accept: i
			}, n);
			a.currentNode = n[n.length - 1].nextElementSibling;
			let o = a.previousNode();
			return o && Ia(o, !0), o;
		}
	};
}
function Ea(e) {
	return e[0].parentElement;
}
function Da(e) {
	let t = qa.getTreeNode(Ca);
	for (; t && t.scopeRef !== e;) {
		if (t.contain) return !1;
		t = t.parent;
	}
	return !0;
}
function Oa(e) {
	if (!e.form) return Array.from(R(e).querySelectorAll(`input[type="radio"][name="${CSS.escape(e.name)}"]`)).filter((e) => !e.form);
	let t = e.form.elements.namedItem(e.name), n = St(e);
	return t instanceof n.RadioNodeList ? Array.from(t).filter((e) => e instanceof n.HTMLInputElement) : t instanceof n.HTMLInputElement ? [t] : [];
}
function ka(e) {
	if (e.checked) return !0;
	let t = Oa(e);
	return t.length > 0 && !t.some((e) => e.checked);
}
function Aa(e, t) {
	let n = (0, b.useRef)(void 0), r = (0, b.useRef)(void 0);
	H(() => {
		let i = e.current;
		if (!t) {
			r.current &&= (cancelAnimationFrame(r.current), void 0);
			return;
		}
		let a = R(i ? i[0] : void 0), o = (t) => {
			if (t.key !== "Tab" || t.altKey || t.ctrlKey || t.metaKey || !Da(e) || t.isComposing) return;
			let n = jt(a), r = e.current;
			if (!r || !Ma(n, r)) return;
			let i = Wa(Ea(r), { tabbable: !0 }, r);
			if (!n) return;
			i.currentNode = n;
			let o = t.shiftKey ? i.previousNode() : i.nextNode();
			o ||= (i.currentNode = t.shiftKey ? r[r.length - 1].nextElementSibling : r[0].previousElementSibling, t.shiftKey ? i.previousNode() : i.nextNode()), t.preventDefault(), o && (Ia(o, !0), o instanceof St(o).HTMLInputElement && o.select());
		}, s = (t) => {
			(!Ca || Fa(Ca, e)) && Ma(B(t), e.current) ? (Ca = e, n.current = B(t)) : Da(e) && !Na(B(t), e) ? n.current ? Ia(n.current) : Ca && Ca.current && Ra(Ca.current) : Da(e) && (n.current = B(t));
		}, c = (t) => {
			r.current && cancelAnimationFrame(r.current), r.current = requestAnimationFrame(() => {
				let r = Wn(), i = (r === "virtual" || r === null) && an() && rn(), o = jt(a);
				if (!i && o && Da(e) && !Na(o, e)) {
					Ca = e;
					let r = B(t);
					r && r.isConnected ? (n.current = r, Ia(n.current)) : Ca.current && Ra(Ca.current);
				}
			});
		};
		return a.addEventListener("keydown", o, !1), a.addEventListener("focusin", s, !1), i?.forEach((e) => e.addEventListener("focusin", s, !1)), i?.forEach((e) => e.addEventListener("focusout", c, !1)), () => {
			a.removeEventListener("keydown", o, !1), a.removeEventListener("focusin", s, !1), i?.forEach((e) => e.removeEventListener("focusin", s, !1)), i?.forEach((e) => e.removeEventListener("focusout", c, !1));
		};
	}, [e, t]), H(() => () => {
		r.current && cancelAnimationFrame(r.current);
	}, [r]);
}
function ja(e) {
	return Na(e);
}
function Ma(e, t) {
	return !e || !t ? !1 : t.some((t) => z(t, e));
}
function Na(e, t = null) {
	if (e instanceof Element && e.closest("[data-react-aria-top-layer]")) return !0;
	for (let { scopeRef: n } of qa.traverse(qa.getTreeNode(t))) if (n && Ma(e, n.current)) return !0;
	return !1;
}
function Pa(e) {
	return Na(e, Ca);
}
function Fa(e, t) {
	let n = qa.getTreeNode(t)?.parent;
	for (; n;) {
		if (n.scopeRef === e) return !0;
		n = n.parent;
	}
	return !1;
}
function Ia(e, t = !1) {
	if (e != null && !t) try {
		er(e);
	} catch {}
	else if (e != null) try {
		e.focus();
	} catch {}
}
function La(e, t = !0) {
	let n = e[0].previousElementSibling, r = Ea(e), i = Wa(r, { tabbable: t }, e);
	i.currentNode = n;
	let a = i.nextNode();
	return t && !a && (r = Ea(e), i = Wa(r, { tabbable: !1 }, e), i.currentNode = n, a = i.nextNode()), a;
}
function Ra(e, t = !0) {
	Ia(La(e, t));
}
function za(e, t) {
	let n = b.useRef(t);
	(0, b.useEffect)(() => {
		n.current && (Ca = e, !Ma(jt(R(e.current ? e.current[0] : void 0)), Ca.current) && e.current && Ra(e.current)), n.current = !1;
	}, [e]);
}
function Ba(e, t, n) {
	H(() => {
		if (t || n) return;
		let r = e.current, i = R(r ? r[0] : void 0), a = (t) => {
			let n = B(t);
			Ma(n, e.current) ? Ca = e : ja(n) || (Ca = null);
		};
		return i.addEventListener("focusin", a, !1), r?.forEach((e) => e.addEventListener("focusin", a, !1)), () => {
			i.removeEventListener("focusin", a, !1), r?.forEach((e) => e.removeEventListener("focusin", a, !1));
		};
	}, [
		e,
		t,
		n
	]);
}
function Va(e) {
	let t = qa.getTreeNode(Ca);
	for (; t && t.scopeRef !== e;) {
		if (t.nodeToRestore) return !1;
		t = t.parent;
	}
	return t?.scopeRef === e;
}
function Ha(e, t, n) {
	let r = (0, b.useRef)(typeof document < "u" ? jt(R(e.current ? e.current[0] : void 0)) : null);
	H(() => {
		let r = e.current, i = R(r ? r[0] : void 0);
		if (!t || n) return;
		let a = () => {
			(!Ca || Fa(Ca, e)) && Ma(jt(i), e.current) && (Ca = e);
		};
		return i.addEventListener("focusin", a, !1), r?.forEach((e) => e.addEventListener("focusin", a, !1)), () => {
			i.removeEventListener("focusin", a, !1), r?.forEach((e) => e.removeEventListener("focusin", a, !1));
		};
	}, [e, n]), H(() => {
		let r = R(e.current ? e.current[0] : void 0);
		if (!t) return;
		let i = (t) => {
			if (t.key !== "Tab" || t.altKey || t.ctrlKey || t.metaKey || !Da(e) || t.isComposing) return;
			let n = r.activeElement;
			if (!Na(n, e) || !Va(e)) return;
			let i = qa.getTreeNode(e);
			if (!i) return;
			let a = i.nodeToRestore, o = Wa(r.body, { tabbable: !0 });
			o.currentNode = n;
			let s = t.shiftKey ? o.previousNode() : o.nextNode();
			if ((!a || !a.isConnected || a === r.body) && (a = void 0, i.nodeToRestore = void 0), (!s || !Na(s, e)) && a) {
				o.currentNode = a;
				do
					s = t.shiftKey ? o.previousNode() : o.nextNode();
				while (Na(s, e));
				t.preventDefault(), t.stopPropagation(), s ? Ia(s, !0) : ja(a) ? Ia(a, !0) : n.blur();
			}
		};
		return n || r.addEventListener("keydown", i, !0), () => {
			n || r.removeEventListener("keydown", i, !0);
		};
	}, [
		e,
		t,
		n
	]), H(() => {
		let n = R(e.current ? e.current[0] : void 0);
		if (!t) return;
		let i = qa.getTreeNode(e);
		if (i) return i.nodeToRestore = r.current ?? void 0, () => {
			let r = qa.getTreeNode(e);
			if (!r) return;
			let i = r.nodeToRestore, a = jt(n);
			if (t && i && (a && Na(a, e) || a === n.body && Va(e))) {
				let t = qa.clone();
				requestAnimationFrame(() => {
					if (n.activeElement === n.body) {
						let n = t.getTreeNode(e);
						for (; n;) {
							if (n.nodeToRestore && n.nodeToRestore.isConnected) {
								Ua(n.nodeToRestore);
								return;
							}
							n = n.parent;
						}
						for (n = t.getTreeNode(e); n;) {
							if (n.scopeRef && n.scopeRef.current && qa.getTreeNode(n.scopeRef)) {
								let e = La(n.scopeRef.current, !0);
								if (e) {
									Ua(e);
									return;
								}
							}
							n = n.parent;
						}
					}
				});
			}
		};
	}, [e, t]);
}
function Ua(e) {
	e.dispatchEvent(new CustomEvent(Sa, {
		bubbles: !0,
		cancelable: !0
	})) && Ia(e);
}
function Wa(e, t, n) {
	let r = t?.tabbable ? V : Vt, i = R(e?.nodeType === Node.ELEMENT_NODE ? e : null), a = ba(i, e || i, NodeFilter.SHOW_ELEMENT, { acceptNode(e) {
		return z(t?.from, e) || t?.tabbable && e.tagName === "INPUT" && e.getAttribute("type") === "radio" && (!ka(e) || a.currentNode.tagName === "INPUT" && a.currentNode.type === "radio" && a.currentNode.name === e.name) ? NodeFilter.FILTER_REJECT : r(e) && (!n || Ma(e, n)) && (!t?.accept || t.accept(e)) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
	} });
	return t?.from && (a.currentNode = t.from), a;
}
var Ga = class e {
	constructor() {
		this.fastMap = /* @__PURE__ */ new Map(), this.root = new Ka({ scopeRef: null }), this.fastMap.set(null, this.root);
	}
	get size() {
		return this.fastMap.size;
	}
	getTreeNode(e) {
		return this.fastMap.get(e);
	}
	addTreeNode(e, t, n) {
		let r = this.fastMap.get(t ?? null);
		if (!r) return;
		let i = new Ka({ scopeRef: e });
		r.addChild(i), i.parent = r, this.fastMap.set(e, i), n && (i.nodeToRestore = n);
	}
	addNode(e) {
		this.fastMap.set(e.scopeRef, e);
	}
	removeTreeNode(e) {
		if (e === null) return;
		let t = this.fastMap.get(e);
		if (!t) return;
		let n = t.parent;
		for (let e of this.traverse()) e !== t && t.nodeToRestore && e.nodeToRestore && t.scopeRef && t.scopeRef.current && Ma(e.nodeToRestore, t.scopeRef.current) && (e.nodeToRestore = t.nodeToRestore);
		let r = t.children;
		n && (n.removeChild(t), r.size > 0 && r.forEach((e) => n && n.addChild(e))), this.fastMap.delete(t.scopeRef);
	}
	*traverse(e = this.root) {
		if (e.scopeRef != null && (yield e), e.children.size > 0) for (let t of e.children) yield* this.traverse(t);
	}
	clone() {
		let t = new e();
		for (let e of this.traverse()) t.addTreeNode(e.scopeRef, e.parent?.scopeRef ?? null, e.nodeToRestore);
		return t;
	}
}, Ka = class {
	constructor(e) {
		this.children = /* @__PURE__ */ new Set(), this.contain = !1, this.scopeRef = e.scopeRef;
	}
	addChild(e) {
		this.children.add(e), e.parent = this;
	}
	removeChild(e) {
		this.children.delete(e), e.parent = void 0;
	}
}, qa = new Ga(), Ja = 7e3, Ya = null;
function Xa(e, t = "assertive", n = Ja) {
	Ya ? Ya.announce(e, t, n) : (Ya = new Za(), (typeof IS_REACT_ACT_ENVIRONMENT == "boolean" ? IS_REACT_ACT_ENVIRONMENT : typeof jest < "u") ? Ya.announce(e, t, n) : setTimeout(() => {
		Ya?.isAttached() && Ya?.announce(e, t, n);
	}, 100));
}
var Za = class {
	constructor() {
		this.node = null, this.assertiveLog = null, this.politeLog = null, typeof document < "u" && (this.node = document.createElement("div"), this.node.dataset.liveAnnouncer = "true", Object.assign(this.node.style, {
			border: 0,
			clip: "rect(0 0 0 0)",
			clipPath: "inset(50%)",
			height: "1px",
			margin: "-1px",
			overflow: "hidden",
			padding: 0,
			position: "absolute",
			width: "1px",
			whiteSpace: "nowrap"
		}), this.assertiveLog = this.createLog("assertive"), this.node.appendChild(this.assertiveLog), this.politeLog = this.createLog("polite"), this.node.appendChild(this.politeLog), document.body.prepend(this.node));
	}
	isAttached() {
		return this.node?.isConnected;
	}
	createLog(e) {
		let t = document.createElement("div");
		return t.setAttribute("role", "log"), t.setAttribute("aria-live", e), t.setAttribute("aria-relevant", "additions"), t;
	}
	destroy() {
		this.node &&= (document.body.removeChild(this.node), null);
	}
	announce(e, t = "assertive", n = Ja) {
		if (!this.node) return;
		let r = document.createElement("div");
		typeof e == "object" ? (r.setAttribute("role", "img"), r.setAttribute("aria-labelledby", e["aria-labelledby"])) : r.textContent = e, t === "assertive" ? this.assertiveLog?.appendChild(r) : this.politeLog?.appendChild(r), e !== "" && setTimeout(() => {
			r.remove();
		}, n);
	}
	clear(e) {
		this.node && ((!e || e === "assertive") && this.assertiveLog && (this.assertiveLog.innerHTML = ""), (!e || e === "polite") && this.politeLog && (this.politeLog.innerHTML = ""));
	}
};
//#endregion
//#region node_modules/react-aria/dist/private/utils/isScrollable.mjs
function Qa(e, t) {
	if (!e) return !1;
	let n = window.getComputedStyle(e), r = document.scrollingElement || document.documentElement, i = /(auto|scroll)/.test(n.overflow + n.overflowX + n.overflowY);
	return e === r && n.overflow !== "hidden" && (i = !0), i && t && (i = e.scrollHeight !== e.clientHeight || e.scrollWidth !== e.clientWidth), i;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getScrollParent.mjs
function $a(e, t) {
	let n = e;
	for (Qa(n, t) && (n = n.parentElement); n && !Qa(n, t);) n = n.parentElement;
	return n || document.scrollingElement || document.documentElement;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getScrollParents.mjs
function eo(e, t) {
	let n = [], r = document.scrollingElement || document.documentElement;
	for (; e && (Qa(e, t) && n.push(e), e !== r);) e = e.parentElement;
	return n;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/scrollIntoView.mjs
function to(e, t, n = {}) {
	e !== t && no(e, t, t.getBoundingClientRect(), n);
}
function no(e, t, n, r = {}) {
	let { block: i = "nearest", inline: a = "nearest" } = r, o = e.scrollTop, s = e.scrollLeft, c = e.getBoundingClientRect(), l = window.getComputedStyle(t), u = window.getComputedStyle(e), d = document.scrollingElement || document.documentElement, f = e === d, p = e === d ? 0 : c.top, m = e === d ? e.clientHeight : c.bottom, h = e === d ? 0 : c.left, g = e === d ? e.clientWidth : c.right, _ = parseFloat(l.scrollMarginTop) || 0, v = parseFloat(l.scrollMarginBottom) || 0, y = parseFloat(l.scrollMarginLeft) || 0, b = parseFloat(l.scrollMarginRight) || 0, x = parseFloat(u.scrollPaddingTop) || 0, S = parseFloat(u.scrollPaddingBottom) || 0, C = parseFloat(u.scrollPaddingLeft) || 0, w = parseFloat(u.scrollPaddingRight) || 0, T = parseFloat(u.borderTopWidth) || 0, E = parseFloat(u.borderBottomWidth) || 0, D = parseFloat(u.borderLeftWidth) || 0, O = parseFloat(u.borderRightWidth) || 0, k = n.top - _, A = n.bottom + v, j = n.left - y, M = n.right + b, N = e === d ? 0 : D + O, ee = e === d ? 0 : T + E, te = e === d ? 0 : e.offsetWidth - e.clientWidth - N, P = e === d ? 0 : e.offsetHeight - e.clientHeight - ee, ne = p + (f ? 0 : T) + x, F = m - (f ? 0 : E) - S - P, re = h + (f ? 0 : D) + C, ie = g - (f ? 0 : O) - w;
	en() && nn() || u.direction === "ltr" ? ie -= te : u.direction === "rtl" && (re += te);
	let ae = k < ne || A > F, oe = j < re || M > ie;
	if (ae && i === "start") o += k - ne;
	else if (ae && i === "center") o += (k + A) / 2 - (ne + F) / 2;
	else if (ae && i === "end") o += A - F;
	else if (ae && i === "nearest") {
		let e = k - ne, t = A - F;
		o += Math.abs(e) <= Math.abs(t) ? e : t;
	}
	if (oe && a === "start") s += j - re;
	else if (oe && a === "center") s += (j + M) / 2 - (re + ie) / 2;
	else if (oe && a === "end") s += M - ie;
	else if (oe && a === "nearest") {
		let e = j - re, t = M - ie;
		s += Math.abs(e) <= Math.abs(t) ? e : t;
	}
	e.scrollTo({
		left: s,
		top: o
	});
}
function ro(e, t = {}) {
	let { containingElement: n } = t;
	if (e && e.isConnected) {
		let t = document.scrollingElement || document.documentElement;
		if (window.getComputedStyle(t).overflow !== "hidden") {
			let { left: t, top: r } = e.getBoundingClientRect();
			e?.scrollIntoView?.({ block: "nearest" });
			let { left: i, top: a } = e.getBoundingClientRect();
			(Math.abs(t - i) > 1 || Math.abs(r - a) > 1) && (n?.scrollIntoView?.({
				block: "center",
				inline: "center"
			}), e.scrollIntoView?.({ block: "nearest" }));
		} else {
			let { left: t, top: r } = e.getBoundingClientRect(), i = eo(e, !0);
			for (let t of i) to(t, e);
			let { left: a, top: o } = e.getBoundingClientRect();
			if (Math.abs(t - a) > 1 || Math.abs(r - o) > 1) {
				i = n ? eo(n, !0) : [];
				for (let e of i) to(e, n, {
					block: "center",
					inline: "center"
				});
				for (let t of eo(e, !0)) to(t, e);
			}
		}
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useDescription.mjs
var io = 0, ao = /* @__PURE__ */ new Map();
function oo(e) {
	let [t, n] = (0, b.useState)();
	return H(() => {
		if (!e) return;
		let t = ao.get(e);
		if (t) n(t.element.id);
		else {
			let r = `react-aria-description-${io++}`;
			n(r);
			let i = document.createElement("div");
			i.id = r, i.style.display = "none", i.textContent = e, document.body.appendChild(i), t = {
				refCount: 0,
				element: i
			}, ao.set(e, t);
		}
		return t.refCount++, () => {
			t && --t.refCount === 0 && (t.element.remove(), ao.delete(e));
		};
	}, [e]), { "aria-describedby": e ? t : void 0 };
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useFormReset.mjs
function so(e, t, n) {
	let r = hi((e) => {
		n && !e.defaultPrevented && n(t);
	});
	(0, b.useEffect)(() => {
		let t = e?.current?.form;
		return t?.addEventListener("reset", r), () => {
			t?.removeEventListener("reset", r);
		};
	}, [e]);
}
//#endregion
//#region node_modules/react-aria/dist/private/form/useFormValidation.mjs
function co(e, t, n) {
	let { validationBehavior: r, focus: i } = e;
	H(() => {
		if (r === "native" && n?.current && "setCustomValidity" in n.current && !n.current.disabled) {
			let e = t.realtimeValidation.isInvalid ? t.realtimeValidation.validationErrors.join(" ") || "Invalid value." : "";
			n.current.setCustomValidity(e), n.current.hasAttribute("title") || (n.current.title = ""), t.realtimeValidation.isInvalid || t.updateValidation(uo(n.current));
		}
	});
	let a = (0, b.useRef)(!1), o = hi(() => {
		a.current || t.resetValidation();
	}), s = hi((e) => {
		t.displayValidation.isInvalid || t.commitValidation();
		let r = n?.current?.form;
		!e.defaultPrevented && n && r && fo(r) === n.current && (i ? i() : n.current?.focus(), Gn("keyboard")), e.preventDefault();
	}), c = hi(() => {
		t.commitValidation();
	});
	(0, b.useEffect)(() => {
		let e = n?.current;
		if (!e) return;
		let t = e.form, r = t?.reset;
		return t && (t.reset = () => {
			a.current = !window.event || window.event.type === "message" && B(window.event) instanceof MessagePort, r?.call(t), a.current = !1;
		}), e.addEventListener("invalid", s), e.addEventListener("change", c), t?.addEventListener("reset", o), () => {
			e.removeEventListener("invalid", s), e.removeEventListener("change", c), t?.removeEventListener("reset", o), t && (t.reset = r);
		};
	}, [n, r]);
}
function lo(e) {
	let t = e.validity;
	return {
		badInput: t.badInput,
		customError: t.customError,
		patternMismatch: t.patternMismatch,
		rangeOverflow: t.rangeOverflow,
		rangeUnderflow: t.rangeUnderflow,
		stepMismatch: t.stepMismatch,
		tooLong: t.tooLong,
		tooShort: t.tooShort,
		typeMismatch: t.typeMismatch,
		valueMissing: t.valueMissing,
		valid: t.valid
	};
}
function uo(e) {
	return {
		isInvalid: !e.validity.valid,
		validationDetails: lo(e),
		validationErrors: e.validationMessage ? [e.validationMessage] : []
	};
}
function fo(e) {
	for (let t = 0; t < e.elements.length; t++) {
		let n = e.elements[t];
		if (n.validity?.valid === !1) return n;
	}
	return null;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useSlot.mjs
function po(e = !0) {
	let [t, n] = (0, b.useState)(e), r = (0, b.useRef)(!1), i = (0, b.useCallback)((e) => {
		r.current = !0, n(!!e);
	}, []);
	return H(() => {
		r.current || n(!1);
	}, []), [i, t];
}
function mo(e = !0) {
	let t = sr(), [n, r] = po(e);
	return {
		id: r ? t : void 0,
		ref: n
	};
}
//#endregion
//#region node_modules/react-stately/dist/private/form/useFormValidationState.mjs
var ho = {
	badInput: !1,
	customError: !1,
	patternMismatch: !1,
	rangeOverflow: !1,
	rangeUnderflow: !1,
	stepMismatch: !1,
	tooLong: !1,
	tooShort: !1,
	typeMismatch: !1,
	valueMissing: !1,
	valid: !0
}, go = {
	...ho,
	customError: !0,
	valid: !1
}, _o = {
	isInvalid: !1,
	validationDetails: ho,
	validationErrors: []
}, vo = (0, b.createContext)({}), yo = "__reactAriaFormValidationState";
function bo(e) {
	if (e.__reactAriaFormValidationState) {
		let { realtimeValidation: t, displayValidation: n, updateValidation: r, resetValidation: i, commitValidation: a } = e[yo];
		return {
			realtimeValidation: t,
			displayValidation: n,
			updateValidation: r,
			resetValidation: i,
			commitValidation: a
		};
	}
	return xo(e);
}
function xo(e) {
	let { isInvalid: t, validationState: n, name: r, value: i, builtinValidation: a, validate: o, validationBehavior: s = "aria" } = e;
	n && (t ||= n === "invalid");
	let c = t === void 0 ? null : {
		isInvalid: t,
		validationErrors: [],
		validationDetails: go
	}, l = (0, b.useMemo)(() => !o || i == null ? null : wo(Co(o, i)), [o, i]);
	a?.validationDetails.valid && (a = void 0);
	let u = (0, b.useContext)(vo), d = (0, b.useMemo)(() => r ? Array.isArray(r) ? r.flatMap((e) => So(u[e])) : So(u[r]) : [], [u, r]), [f, p] = (0, b.useState)(u), [m, h] = (0, b.useState)(!1);
	u !== f && (p(u), h(!1));
	let g = (0, b.useMemo)(() => wo(m ? [] : d), [m, d]), _ = (0, b.useRef)(_o), [v, y] = (0, b.useState)(_o), x = (0, b.useRef)(_o), S = () => {
		if (!C) return;
		w(!1);
		let e = l || a || _.current;
		To(e, x.current) || (x.current = e, y(e));
	}, [C, w] = (0, b.useState)(!1);
	return (0, b.useEffect)(S), {
		realtimeValidation: c || g || l || a || _o,
		displayValidation: s === "native" ? c || g || v : c || g || l || a || v,
		updateValidation(e) {
			s === "aria" && !To(v, e) ? y(e) : _.current = e;
		},
		resetValidation() {
			let e = _o;
			To(e, x.current) || (x.current = e, y(e)), s === "native" && w(!1), h(!0);
		},
		commitValidation() {
			s === "native" && w(!0), h(!0);
		}
	};
}
function So(e) {
	return e ? Array.isArray(e) ? e : [e] : [];
}
function Co(e, t) {
	if (typeof e == "function") {
		let n = e(t);
		if (n && typeof n != "boolean") return So(n);
	}
	return [];
}
function wo(e) {
	return e.length ? {
		isInvalid: !0,
		validationErrors: e,
		validationDetails: go
	} : null;
}
function To(e, t) {
	return e === t || !!e && !!t && e.isInvalid === t.isInvalid && e.validationErrors.length === t.validationErrors.length && e.validationErrors.every((e, n) => e === t.validationErrors[n]) && Object.entries(e.validationDetails).every(([e, n]) => t.validationDetails[e] === n);
}
//#endregion
//#region node_modules/react-aria/dist/private/toggle/useToggle.mjs
function Eo(e, t, n) {
	let { isDisabled: r = !1, isReadOnly: i = !1, value: a, name: o, form: s, children: c, isRequired: l, validationBehavior: u = "aria", "aria-label": d, "aria-labelledby": f, "aria-describedby": p, onPressStart: m, onPressEnd: h, onPressChange: g, onPress: _, onPressUp: v, onClick: y } = e, x = bo({
		...e,
		value: t.isSelected
	}), { isInvalid: S, validationErrors: C, validationDetails: w } = x.displayValidation;
	co(e, x, n);
	let T = (e) => {
		e.stopPropagation(), t.setSelected(B(e).checked);
	}, { pressProps: E, isPressed: D } = ua({
		onPressStart: m,
		onPressEnd: h,
		onPressChange: g,
		onPress: _,
		onPressUp: v,
		onClick: y,
		isDisabled: r
	}), [O, k] = (0, b.useState)(!1), { pressProps: A } = ua({
		onPressStart(e) {
			if (e.pointerType === "keyboard" || e.pointerType === "virtual") {
				e.continuePropagation();
				return;
			}
			m?.(e), g?.(!0), k(!0);
		},
		onPressEnd(e) {
			if (e.pointerType === "keyboard" || e.pointerType === "virtual") {
				e.continuePropagation();
				return;
			}
			h?.(e), g?.(!1), k(!1);
		},
		onPressUp(e) {
			if (e.pointerType === "keyboard" || e.pointerType === "virtual") {
				e.continuePropagation();
				return;
			}
			v?.(e);
		},
		onClick: y,
		onPress(r) {
			if (r.pointerType === "keyboard" || r.pointerType === "virtual") {
				r.continuePropagation();
				return;
			}
			_?.(r), t.toggle(), n.current?.focus();
			let { [yo]: i } = e, { commitValidation: a } = i || x;
			a();
		},
		isDisabled: r || i
	}), { focusableProps: j } = Nr(e, n), M = U(E, j), N = Yi(e, { labelable: !0 });
	so(n, t.defaultSelected, t.setSelected);
	let ee = mo(), te = mo();
	return {
		labelProps: U(A, { onClick: (e) => e.preventDefault() }),
		inputProps: U(N, {
			checked: t.isSelected,
			"aria-required": l && u === "aria" || void 0,
			required: l && u === "native",
			"aria-invalid": S || e.validationState === "invalid" || void 0,
			"aria-errormessage": e["aria-errormessage"],
			"aria-controls": e["aria-controls"],
			"aria-readonly": i || void 0,
			"aria-describedby": [
				ee.id,
				te.id,
				p
			].filter(Boolean).join(" ") || void 0,
			onChange: T,
			disabled: r,
			...a == null ? {} : { value: a },
			name: o,
			form: s,
			type: "checkbox",
			...M
		}),
		descriptionProps: ee,
		errorMessageProps: te,
		isSelected: t.isSelected,
		isPressed: D || O,
		isDisabled: r,
		isReadOnly: i,
		isInvalid: S || e.validationState === "invalid",
		validationErrors: C,
		validationDetails: w
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/checkbox/useCheckbox.mjs
function Do(e, t, n) {
	let { labelProps: r, inputProps: i, descriptionProps: a, errorMessageProps: o, isSelected: s, isPressed: c, isDisabled: l, isReadOnly: u, isInvalid: d, validationErrors: f, validationDetails: p } = Eo(e, t, n), { isIndeterminate: m } = e;
	return (0, b.useEffect)(() => {
		n.current && (n.current.indeterminate = !!m);
	}), {
		labelProps: U(r, (0, b.useMemo)(() => ({ onMouseDown: (e) => e.preventDefault() }), [])),
		inputProps: i,
		descriptionProps: a,
		errorMessageProps: o,
		isSelected: s,
		isPressed: c,
		isDisabled: l,
		isReadOnly: u,
		isInvalid: d,
		validationErrors: f,
		validationDetails: p
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/checkbox/utils.mjs
var Oo = /* @__PURE__ */ new WeakMap();
//#endregion
//#region node_modules/react-aria/dist/private/label/useLabel.mjs
function ko(e) {
	let { id: t, label: n, "aria-labelledby": r, "aria-label": i, labelElementType: a = "label" } = e;
	t = sr(t);
	let o = sr(), s = {};
	n && (r = r ? `${o} ${r}` : o, s = {
		id: o,
		htmlFor: a === "label" ? t : void 0
	});
	let c = _i({
		id: t,
		"aria-label": i,
		"aria-labelledby": r
	});
	return {
		labelProps: s,
		fieldProps: c
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/label/useField.mjs
function Ao(e) {
	let { description: t, errorMessage: n, isInvalid: r, validationState: i } = e, { labelProps: a, fieldProps: o } = ko(e), s = lr([
		!!t,
		!!n,
		r,
		i
	]), c = lr([
		!!t,
		!!n,
		r,
		i
	]);
	return o = U(o, { "aria-describedby": [
		s,
		c,
		e["aria-describedby"]
	].filter(Boolean).join(" ") || void 0 }), {
		labelProps: a,
		fieldProps: o,
		descriptionProps: { id: s },
		errorMessageProps: { id: c }
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocusWithin.mjs
function jo(e) {
	let { isDisabled: t, onBlurWithin: n, onFocusWithin: r, onFocusWithinChange: i } = e, a = (0, b.useRef)({ isFocusWithin: !1 }), { addGlobalListener: o, removeAllGlobalListeners: s } = ia(), c = (0, b.useCallback)((e) => {
		z(e.currentTarget, B(e)) && a.current.isFocusWithin && !z(e.currentTarget, e.relatedTarget) && (a.current.isFocusWithin = !1, s(), n && n(e), i && i(!1));
	}, [
		n,
		i,
		a,
		s
	]), l = Gt(c), u = (0, b.useCallback)((e) => {
		if (!z(e.currentTarget, B(e))) return;
		let t = B(e), n = R(t), s = jt(n);
		if (!a.current.isFocusWithin && s === t) {
			r && r(e), i && i(!0), a.current.isFocusWithin = !0, l(e);
			let t = e.currentTarget;
			o(n, "focus", (e) => {
				let r = B(e);
				if (a.current.isFocusWithin && !z(t, r)) {
					let e = new n.defaultView.FocusEvent("blur", { relatedTarget: r });
					Wt(e, t);
					let i = Ut(e);
					c(i);
				}
			}, { capture: !0 });
		}
	}, [
		r,
		i,
		l,
		o,
		c
	]);
	return t ? { focusWithinProps: {
		onFocus: void 0,
		onBlur: void 0
	} } : { focusWithinProps: {
		onFocus: u,
		onBlur: c
	} };
}
//#endregion
//#region node_modules/react-stately/dist/private/utils/useControlledState.mjs
var Mo = typeof document < "u" ? b.useInsertionEffect ?? b.useLayoutEffect : () => {};
function No(e, t, n) {
	let [r, i] = (0, b.useState)(e || t), a = (0, b.useRef)(r), o = (0, b.useRef)(e !== void 0), s = e !== void 0;
	(0, b.useEffect)(() => {
		o.current, o.current = s;
	}, [s]);
	let c = s ? e : r;
	Mo(() => {
		a.current = c;
	});
	let [, l] = (0, b.useReducer)(() => ({}), {});
	return [c, (0, b.useCallback)((e, ...t) => {
		let r = typeof e == "function" ? e(a.current) : e;
		Object.is(a.current, r) || (a.current = r, i(r), l(), n?.(r, ...t));
	}, [n])];
}
//#endregion
//#region node_modules/react-stately/dist/private/toggle/useToggleState.mjs
function Po(e = {}) {
	let { isReadOnly: t } = e, [n, r] = No(e.isSelected, e.defaultSelected || !1, e.onChange), [i] = (0, b.useState)(n);
	function a(e) {
		t || r(e);
	}
	function o() {
		t || r(!n);
	}
	return {
		isSelected: n,
		defaultSelected: e.defaultSelected ?? i,
		setSelected: a,
		toggle: o
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/checkbox/useCheckboxGroupItem.mjs
function Fo(e, t, n) {
	let r = Po({
		isReadOnly: e.isReadOnly || t.isReadOnly,
		isSelected: t.isSelected(e.value),
		defaultSelected: t.defaultValue.includes(e.value),
		onChange(n) {
			n ? t.addValue(e.value) : t.removeValue(e.value), e.onChange && e.onChange(n);
		}
	}), { name: i, form: a, descriptionId: o, errorMessageId: s, validationBehavior: c } = Oo.get(t);
	c = e.validationBehavior ?? c;
	let { realtimeValidation: l } = bo({
		...e,
		value: r.isSelected,
		name: void 0,
		validationBehavior: "aria"
	}), u = (0, b.useRef)(_o), d = () => {
		t.setInvalid(e.value, l.isInvalid ? l : u.current);
	};
	(0, b.useEffect)(d);
	let f = t.realtimeValidation.isInvalid ? t.realtimeValidation : l, p = c === "native" ? t.displayValidation : f, m = Do({
		...e,
		isReadOnly: e.isReadOnly || t.isReadOnly,
		isDisabled: e.isDisabled || t.isDisabled,
		name: e.name || i,
		form: e.form || a,
		isRequired: e.isRequired ?? t.isRequired,
		validationBehavior: c,
		[yo]: {
			realtimeValidation: f,
			displayValidation: p,
			resetValidation: t.resetValidation,
			commitValidation: t.commitValidation,
			updateValidation(e) {
				u.current = e, d();
			}
		}
	}, r, n);
	return {
		...m,
		inputProps: {
			...m.inputProps,
			"aria-describedby": [
				m.inputProps["aria-describedby"],
				t.isInvalid ? s : null,
				o
			].filter(Boolean).join(" ") || void 0
		}
	};
}
//#endregion
//#region node_modules/react-stately/dist/private/utils/number.mjs
function Io(e, t = -Infinity, n = Infinity) {
	return Math.min(Math.max(e, t), n);
}
//#endregion
//#region node_modules/react-aria/dist/private/visually-hidden/VisuallyHidden.mjs
var Lo = {
	border: 0,
	clip: "rect(0 0 0 0)",
	clipPath: "inset(50%)",
	height: "1px",
	margin: "-1px",
	overflow: "hidden",
	padding: 0,
	position: "absolute",
	width: "1px",
	whiteSpace: "nowrap"
};
function G(e = {}) {
	let { style: t, isFocusable: n } = e, [r, i] = (0, b.useState)(!1), { focusWithinProps: a } = jo({
		isDisabled: !n,
		onFocusWithinChange: (e) => i(e)
	}), o = (0, b.useMemo)(() => r ? t : t ? {
		...Lo,
		...t
	} : Lo, [r]);
	return { visuallyHiddenProps: {
		...a,
		style: o
	} };
}
function Ro(e) {
	let { children: t, elementType: n = "div", isFocusable: r, style: i, ...a } = e, { visuallyHiddenProps: o } = G(e);
	return /*#__PURE__*/ b.createElement(n, U(a, o), t);
}
//#endregion
//#region node_modules/react-aria/dist/private/textfield/useTextField.mjs
function zo(e, t) {
	let { inputElementType: n = "input", isDisabled: r = !1, isRequired: i = !1, isReadOnly: a = !1, type: o = "text", validationBehavior: s = "aria" } = e, [c, l] = No(e.value, e.defaultValue || "", e.onChange), { focusableProps: u } = Nr(e, t), d = bo({
		...e,
		value: c
	}), { isInvalid: f, validationErrors: p, validationDetails: m } = d.displayValidation, { labelProps: h, fieldProps: g, descriptionProps: _, errorMessageProps: v } = Ao({
		...e,
		isInvalid: f,
		errorMessage: e.errorMessage || p
	}), y = Yi(e, { labelable: !0 }), x = {
		type: o,
		pattern: e.pattern
	}, [S] = (0, b.useState)(c);
	return so(t, e.defaultValue ?? S, l), co(e, d, t), {
		labelProps: h,
		inputProps: U(y, n === "input" ? x : void 0, {
			disabled: r,
			readOnly: a,
			required: i && s === "native",
			"aria-required": i && s === "aria" || void 0,
			"aria-invalid": f || void 0,
			"aria-errormessage": e["aria-errormessage"],
			"aria-activedescendant": e["aria-activedescendant"],
			"aria-autocomplete": e["aria-autocomplete"],
			"aria-haspopup": e["aria-haspopup"],
			"aria-controls": e["aria-controls"],
			value: c,
			onChange: (e) => l(B(e).value),
			autoComplete: e.autoComplete,
			autoCapitalize: e.autoCapitalize,
			maxLength: e.maxLength,
			minLength: e.minLength,
			name: e.name,
			form: e.form,
			placeholder: e.placeholder,
			inputMode: e.inputMode,
			autoCorrect: e.autoCorrect,
			spellCheck: e.spellCheck,
			enterKeyHint: e.enterKeyHint,
			onCopy: e.onCopy,
			onCut: e.onCut,
			onPaste: e.onPaste,
			onCompositionEnd: e.onCompositionEnd,
			onCompositionStart: e.onCompositionStart,
			onCompositionUpdate: e.onCompositionUpdate,
			onSelect: e.onSelect,
			onBeforeInput: e.onBeforeInput,
			onInput: e.onInput,
			...u,
			...g
		}),
		descriptionProps: _,
		errorMessageProps: v,
		isInvalid: f,
		validationErrors: p,
		validationDetails: m
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/ariaHideOutside.mjs
var Bo = typeof HTMLElement < "u" && "inert" in HTMLElement.prototype;
function Vo(e) {
	return e.dataset.liveAnnouncer === "true" || e.dataset.reactAriaTopLayer !== void 0;
}
var Ho = /* @__PURE__ */ new WeakMap(), Uo = [];
function Wo(e, t) {
	let n = St(e?.[0]), r = t instanceof n.Element ? { root: t } : t, i = r?.root ?? document.body, a = r?.shouldUseInert && Bo, o = new Set(e), s = /* @__PURE__ */ new Set(), c = (e) => a && e instanceof n.HTMLElement ? e.inert : e.getAttribute("aria-hidden") === "true", l = (e, t) => {
		a && e instanceof n.HTMLElement ? e.inert = t : t ? e.setAttribute("aria-hidden", "true") : (e.removeAttribute("aria-hidden"), e instanceof n.HTMLElement && (e.inert = !1));
	}, u = /* @__PURE__ */ new Set();
	if (At()) {
		let t = i.getRootNode();
		for (let n of e) {
			let e = n.getRootNode();
			for (; Et(e) && e !== t;) u.add(e), e = e.host.getRootNode();
		}
	}
	let d = (e) => {
		for (let t of e.querySelectorAll("[data-live-announcer], [data-react-aria-top-layer]")) o.add(t);
		let t = (e) => {
			if (s.has(e) || o.has(e) || e.parentElement && s.has(e.parentElement) && e.parentElement.getAttribute("role") !== "row") return NodeFilter.FILTER_REJECT;
			for (let t of o) if (z(e, t)) return NodeFilter.FILTER_SKIP;
			return NodeFilter.FILTER_ACCEPT;
		}, n = ba(R(e), e, NodeFilter.SHOW_ELEMENT, { acceptNode: t }), r = t(e);
		if (r === NodeFilter.FILTER_ACCEPT && f(e), r !== NodeFilter.FILTER_REJECT) {
			let e = n.nextNode();
			for (; e != null;) f(e), e = n.nextNode();
		}
	}, f = (e) => {
		let t = Ho.get(e) ?? 0;
		c(e) && t === 0 || (t === 0 && l(e, !0), s.add(e), Ho.set(e, t + 1));
	};
	Uo.length && Uo[Uo.length - 1].disconnect(), d(i);
	let p = new MutationObserver((e) => {
		for (let t of e) if (t.type === "childList") {
			if (t.target.isConnected && ![...o, ...s].some((e) => z(e, t.target))) for (let e of t.addedNodes) (e instanceof HTMLElement || e instanceof SVGElement) && Vo(e) ? o.add(e) : e instanceof Element && d(e);
			if (At()) {
				for (let e of u) if (!e.isConnected) {
					p.disconnect();
					break;
				}
			}
		}
	});
	p.observe(i, {
		childList: !0,
		subtree: !0
	});
	let m = /* @__PURE__ */ new Set();
	if (At()) for (let e of u) {
		let t = new MutationObserver((e) => {
			for (let t of e) if (t.type === "childList") {
				if (t.target.isConnected && ![...o, ...s].some((e) => z(e, t.target))) for (let e of t.addedNodes) (e instanceof HTMLElement || e instanceof SVGElement) && Vo(e) ? o.add(e) : e instanceof Element && d(e);
				if (At()) {
					for (let e of u) if (!e.isConnected) {
						p.disconnect();
						break;
					}
				}
			}
		});
		t.observe(e, {
			childList: !0,
			subtree: !0
		}), m.add(t);
	}
	let h = {
		visibleNodes: o,
		hiddenNodes: s,
		observe() {
			p.observe(i, {
				childList: !0,
				subtree: !0
			});
		},
		disconnect() {
			p.disconnect();
		}
	};
	return Uo.push(h), () => {
		if (p.disconnect(), At()) for (let e of m) e.disconnect();
		for (let e of s) {
			let t = Ho.get(e);
			t != null && (t === 1 ? (l(e, !1), Ho.delete(e)) : Ho.set(e, t - 1));
		}
		h === Uo[Uo.length - 1] ? (Uo.pop(), Uo.length && Uo[Uo.length - 1].observe()) : Uo.splice(Uo.indexOf(h), 1);
	};
}
function Go(e) {
	let t = Uo[Uo.length - 1];
	if (t && !t.visibleNodes.has(e)) return t.visibleNodes.add(e), () => {
		t.visibleNodes.delete(e);
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/utils.mjs
var Ko = /* @__PURE__ */ new WeakMap();
function qo(e) {
	return typeof e == "string" ? e.replace(/\s*/g, "") : "" + e;
}
function Jo(e, t) {
	let n = Ko.get(e);
	if (!n) throw Error("Unknown list");
	return `${n.id}-option-${qo(t)}`;
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/utils.mjs
function Yo(e) {
	return tn() ? e.altKey : e.ctrlKey;
}
function Xo(e, t) {
	let n = `[data-key="${CSS.escape(String(t))}"]`, r = e.current?.dataset.collection;
	return r && (n = `[data-collection="${CSS.escape(r)}"]${n}`), e.current?.querySelector(n);
}
var Zo = /* @__PURE__ */ new WeakMap();
function Qo(e) {
	let t = sr();
	return Zo.set(e, t), t;
}
function $o(e) {
	return Zo.get(e);
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/DOMLayoutDelegate.mjs
var es = class {
	constructor(e) {
		this.ref = e;
	}
	getItemRect(e) {
		let t = this.ref.current;
		if (!t) return null;
		let n = e == null ? null : Xo(this.ref, e);
		if (!n) return null;
		let r = t.getBoundingClientRect(), i = n.getBoundingClientRect();
		return {
			x: i.left - r.left - t.clientLeft + t.scrollLeft,
			y: i.top - r.top - t.clientTop + t.scrollTop,
			width: i.width,
			height: i.height
		};
	}
	getContentSize() {
		let e = this.ref.current;
		return {
			width: e?.scrollWidth ?? 0,
			height: e?.scrollHeight ?? 0
		};
	}
	getVisibleRect() {
		let e = this.ref.current;
		return {
			x: e?.scrollLeft ?? 0,
			y: e?.scrollTop ?? 0,
			width: e?.clientWidth ?? 0,
			height: e?.clientHeight ?? 0
		};
	}
}, ts = class {
	constructor(...e) {
		if (e.length === 1) {
			let t = e[0];
			this.collection = t.collection, this.ref = t.ref, this.collator = t.collator, this.disabledKeys = t.disabledKeys || /* @__PURE__ */ new Set(), this.disabledBehavior = t.disabledBehavior || "all", this.orientation = t.orientation || "vertical", this.direction = t.direction, this.layout = t.layout || "stack", this.layoutDelegate = t.layoutDelegate || new es(t.ref);
		} else this.collection = e[0], this.disabledKeys = e[1], this.ref = e[2], this.collator = e[3], this.layout = "stack", this.orientation = "vertical", this.disabledBehavior = "all", this.layoutDelegate = new es(this.ref);
		this.layout === "stack" && this.orientation === "vertical" && (this.getKeyLeftOf = void 0, this.getKeyRightOf = void 0);
	}
	isDisabled(e) {
		return this.disabledBehavior === "all" && (e.props?.isDisabled || this.disabledKeys.has(e.key)) && e.props?.disabledBehavior !== "selection";
	}
	findNextNonDisabled(e, t, n = !1) {
		let r = e;
		for (; r != null;) {
			let e = this.collection.getItem(r);
			if (e?.type === "item" && (n || !this.isDisabled(e))) return r;
			r = t(r);
		}
		return null;
	}
	getNextKey(e, t) {
		let n = e;
		return n = this.collection.getKeyAfter(n), this.findNextNonDisabled(n, (e) => this.collection.getKeyAfter(e), t?.includeDisabled);
	}
	getPreviousKey(e, t) {
		let n = e;
		return n = this.collection.getKeyBefore(n), this.findNextNonDisabled(n, (e) => this.collection.getKeyBefore(e), t?.includeDisabled);
	}
	findKey(e, t, n) {
		let r = e, i = this.layoutDelegate.getItemRect(r);
		if (!i || r == null) return null;
		let a = i;
		do {
			if (r = t(r), r == null) break;
			i = this.layoutDelegate.getItemRect(r);
		} while (i && n(a, i) && r != null);
		return r;
	}
	isSameRow(e, t) {
		return e.y === t.y || e.x !== t.x;
	}
	isSameColumn(e, t) {
		return e.x === t.x || e.y !== t.y;
	}
	isReversed(e) {
		let t = this.getNextKey(e), n = Xo(this.ref, e);
		if (t != null) {
			let e = Xo(this.ref, t);
			return !n || !e ? !1 : n.getBoundingClientRect().top > e.getBoundingClientRect().top;
		}
		let r = this.getPreviousKey(e);
		if (r != null) {
			let e = Xo(this.ref, r);
			return !n || !e ? !1 : e.getBoundingClientRect().top > n.getBoundingClientRect().top;
		}
		return !1;
	}
	getKeyBelow(e, t) {
		return this.layout === "grid" && this.orientation === "vertical" ? this.findKey(e, (e) => this.getNextKey(e, t), this.isSameRow) : this.orientation === "vertical" && this.isReversed(e) ? this.getPreviousKey(e, t) : this.getNextKey(e, t);
	}
	getKeyAbove(e, t) {
		return this.layout === "grid" && this.orientation === "vertical" ? this.findKey(e, (e) => this.getPreviousKey(e, t), this.isSameRow) : this.orientation === "vertical" && this.isReversed(e) ? this.getNextKey(e, t) : this.getPreviousKey(e, t);
	}
	getNextColumn(e, t, n) {
		return t ? this.getPreviousKey(e, n) : this.getNextKey(e, n);
	}
	getKeyRightOf(e, t) {
		let n = this.direction === "ltr" ? "getKeyRightOf" : "getKeyLeftOf";
		return this.layoutDelegate[n] ? (e = this.layoutDelegate[n](e), this.findNextNonDisabled(e, (e) => this.layoutDelegate[n](e), t?.includeDisabled)) : this.layout === "grid" ? this.orientation === "vertical" ? this.getNextColumn(e, this.direction === "rtl", t) : this.findKey(e, (e) => this.getNextColumn(e, this.direction === "rtl", t), this.isSameColumn) : this.orientation === "horizontal" ? this.getNextColumn(e, this.direction === "rtl", t) : null;
	}
	getKeyLeftOf(e, t) {
		let n = this.direction === "ltr" ? "getKeyLeftOf" : "getKeyRightOf";
		return this.layoutDelegate[n] ? (e = this.layoutDelegate[n](e), this.findNextNonDisabled(e, (e) => this.layoutDelegate[n](e), t?.includeDisabled)) : this.layout === "grid" ? this.orientation === "vertical" ? this.getNextColumn(e, this.direction === "ltr", t) : this.findKey(e, (e) => this.getNextColumn(e, this.direction === "ltr", t), this.isSameColumn) : this.orientation === "horizontal" ? this.getNextColumn(e, this.direction === "ltr", t) : null;
	}
	getFirstKey() {
		let e = this.collection.getFirstKey();
		return this.findNextNonDisabled(e, (e) => this.collection.getKeyAfter(e));
	}
	getLastKey() {
		let e = this.collection.getLastKey();
		return this.findNextNonDisabled(e, (e) => this.collection.getKeyBefore(e));
	}
	getKeyPageAbove(e) {
		let t = this.ref.current, n = this.layoutDelegate.getItemRect(e);
		if (!n) return null;
		let r = this.isReversed(e);
		if (t && !Qa(t)) return this.getFirstKey();
		let i = e;
		if (this.orientation === "horizontal") {
			let e = Math.max(0, n.x + n.width - this.layoutDelegate.getVisibleRect().width);
			for (; n && n.x > e && i != null;) i = this.getKeyAbove(i), n = i == null ? null : this.layoutDelegate.getItemRect(i);
		} else {
			let e = this.layoutDelegate.getVisibleRect(), t = r ? n.y - e.height : Math.max(0, n.y + n.height - e.height);
			for (; n && n.y > t && i != null;) i = this.getKeyAbove(i), n = i == null ? null : this.layoutDelegate.getItemRect(i);
		}
		return i ?? (r ? this.getLastKey() : this.getFirstKey());
	}
	getKeyPageBelow(e) {
		let t = this.ref.current, n = this.layoutDelegate.getItemRect(e);
		if (!n) return null;
		let r = this.isReversed(e);
		if (t && !Qa(t)) return this.getLastKey();
		let i = e;
		if (this.orientation === "horizontal") {
			let e = Math.min(this.layoutDelegate.getContentSize().width, n.x - n.width + this.layoutDelegate.getVisibleRect().width);
			for (; n && n.x < e && i != null;) i = this.getKeyBelow(i), n = i == null ? null : this.layoutDelegate.getItemRect(i);
		} else {
			let e = Math.min(this.layoutDelegate.getContentSize().height, n.y - n.height + this.layoutDelegate.getVisibleRect().height);
			for (; n && n.y < e && i != null;) i = this.getKeyBelow(i), n = i == null ? null : this.layoutDelegate.getItemRect(i);
		}
		return i ?? (r ? this.getFirstKey() : this.getLastKey());
	}
	getKeyForSearch(e, t) {
		if (!this.collator) return null;
		let n = this.collection, r = t || this.getFirstKey();
		for (; r != null;) {
			let t = n.getItem(r);
			if (!t) return null;
			let i = t.textValue.slice(0, e.length);
			if (t.textValue && this.collator.compare(i, e) === 0) return r;
			r = this.getNextKey(r);
		}
		return null;
	}
}, ns = {};
ns = { longPressMessage: "اضغط مطولاً أو اضغط على Alt + السهم لأسفل لفتح القائمة" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/bg-BG.mjs
var rs = {};
rs = { longPressMessage: "Натиснете продължително или натиснете Alt+ стрелка надолу, за да отворите менюто" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/cs-CZ.mjs
var is = {};
is = { longPressMessage: "Dlouhým stiskem nebo stisknutím kláves Alt + šipka dolů otevřete nabídku" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/da-DK.mjs
var as = {};
as = { longPressMessage: "Langt tryk eller tryk på Alt + pil ned for at åbne menuen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/de-DE.mjs
var os = {};
os = { longPressMessage: "Drücken Sie lange oder drücken Sie Alt + Nach-unten, um das Menü zu öffnen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/el-GR.mjs
var ss = {};
ss = { longPressMessage: "Πιέστε παρατεταμένα ή πατήστε Alt + κάτω βέλος για να ανοίξετε το μενού" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/en-US.mjs
var cs = {};
cs = { longPressMessage: "Long press or press Alt + ArrowDown to open menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/es-ES.mjs
var ls = {};
ls = { longPressMessage: "Mantenga pulsado o pulse Alt + flecha abajo para abrir el menú" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/et-EE.mjs
var us = {};
us = { longPressMessage: "Menüü avamiseks vajutage pikalt või vajutage klahve Alt + allanool" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/fi-FI.mjs
var ds = {};
ds = { longPressMessage: "Avaa valikko painamalla pohjassa tai näppäinyhdistelmällä Alt + Alanuoli" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/fr-FR.mjs
var fs = {};
fs = { longPressMessage: "Appuyez de manière prolongée ou appuyez sur Alt\xA0+\xA0Flèche vers le bas pour ouvrir le menu." };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/he-IL.mjs
var ps = {};
ps = { longPressMessage: "לחץ לחיצה ארוכה או הקש Alt + ArrowDown כדי לפתוח את התפריט" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/hr-HR.mjs
var ms = {};
ms = { longPressMessage: "Dugo pritisnite ili pritisnite Alt + strelicu prema dolje za otvaranje izbornika" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/hu-HU.mjs
var hs = {};
hs = { longPressMessage: "Nyomja meg hosszan, vagy nyomja meg az Alt + lefele nyíl gombot a menü megnyitásához" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/it-IT.mjs
var gs = {};
gs = { longPressMessage: "Premi a lungo o premi Alt + Freccia giù per aprire il menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ja-JP.mjs
var _s = {};
_s = { longPressMessage: "長押しまたは Alt+下矢印キーでメニューを開く" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ko-KR.mjs
var vs = {};
vs = { longPressMessage: "길게 누르거나 Alt + 아래쪽 화살표를 눌러 메뉴 열기" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/lt-LT.mjs
var ys = {};
ys = { longPressMessage: "Norėdami atidaryti meniu, nuspaudę palaikykite arba paspauskite „Alt + ArrowDown“." };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/lv-LV.mjs
var bs = {};
bs = { longPressMessage: "Lai atvērtu izvēlni, turiet nospiestu vai nospiediet taustiņu kombināciju Alt + lejupvērstā bultiņa" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/nb-NO.mjs
var xs = {};
xs = { longPressMessage: "Langt trykk eller trykk Alt + PilNed for å åpne menyen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/nl-NL.mjs
var Ss = {};
Ss = { longPressMessage: "Druk lang op Alt + pijl-omlaag of druk op Alt om het menu te openen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/pl-PL.mjs
var Cs = {};
Cs = { longPressMessage: "Naciśnij i przytrzymaj lub naciśnij klawisze Alt + Strzałka w dół, aby otworzyć menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/pt-BR.mjs
var ws = {};
ws = { longPressMessage: "Pressione e segure ou pressione Alt + Seta para baixo para abrir o menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/pt-PT.mjs
var Ts = {};
Ts = { longPressMessage: "Prima continuamente ou prima Alt + Seta Para Baixo para abrir o menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ro-RO.mjs
var Es = {};
Es = { longPressMessage: "Apăsați lung sau apăsați pe Alt + săgeată în jos pentru a deschide meniul" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ru-RU.mjs
var Ds = {};
Ds = { longPressMessage: "Нажмите и удерживайте или нажмите Alt + Стрелка вниз, чтобы открыть меню" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sk-SK.mjs
var Os = {};
Os = { longPressMessage: "Ponuku otvoríte dlhým stlačením alebo stlačením klávesu Alt + klávesu so šípkou nadol" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sl-SI.mjs
var ks = {};
ks = { longPressMessage: "Za odprtje menija pritisnite in držite gumb ali pritisnite Alt+puščica navzdol" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sr-SP.mjs
var As = {};
As = { longPressMessage: "Dugo pritisnite ili pritisnite Alt + strelicu prema dole da otvorite meni" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sv-SE.mjs
var js = {};
js = { longPressMessage: "Håll nedtryckt eller tryck på Alt + pil nedåt för att öppna menyn" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/tr-TR.mjs
var Ms = {};
Ms = { longPressMessage: "Menüyü açmak için uzun basın veya Alt + Aşağı Ok tuşuna basın" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/uk-UA.mjs
var Ns = {};
Ns = { longPressMessage: "Довго або звичайно натисніть комбінацію клавіш Alt і стрілка вниз, щоб відкрити меню" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/zh-CN.mjs
var Ps = {};
Ps = { longPressMessage: "长按或按 Alt + 向下方向键以打开菜单" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/zh-TW.mjs
var Fs = {};
Fs = { longPressMessage: "長按或按 Alt+向下鍵以開啟功能表" };
//#endregion
//#region node_modules/react-aria/dist/private/menu/intlStrings.mjs
var Is = {};
Is = {
	"ar-AE": ns,
	"bg-BG": rs,
	"cs-CZ": is,
	"da-DK": as,
	"de-DE": os,
	"el-GR": ss,
	"en-US": cs,
	"es-ES": ls,
	"et-EE": us,
	"fi-FI": ds,
	"fr-FR": fs,
	"he-IL": ps,
	"hr-HR": ms,
	"hu-HU": hs,
	"it-IT": gs,
	"ja-JP": _s,
	"ko-KR": vs,
	"lt-LT": ys,
	"lv-LV": bs,
	"nb-NO": xs,
	"nl-NL": Ss,
	"pl-PL": Cs,
	"pt-BR": ws,
	"pt-PT": Ts,
	"ro-RO": Es,
	"ru-RU": Ds,
	"sk-SK": Os,
	"sl-SI": ks,
	"sr-SP": As,
	"sv-SE": js,
	"tr-TR": Ms,
	"uk-UA": Ns,
	"zh-CN": Ps,
	"zh-TW": Fs
};
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useLongPress.mjs
var Ls = 500;
function Rs(e) {
	let { isDisabled: t, pointerType: n, onLongPressStart: r, onLongPressEnd: i, onLongPress: a, threshold: o = Ls, accessibilityDescription: s } = e, c = (0, b.useRef)(void 0), { addGlobalListener: l, removeAllGlobalListeners: u } = ia(), d = (e) => n ? e.pointerType === n : e.pointerType === "mouse" || e.pointerType === "touch", { pressProps: f } = ua({
		isDisabled: t,
		onPressStart(e) {
			if (e.continuePropagation(), d(e)) {
				r && r({
					...e,
					type: "longpressstart"
				}), c.current = setTimeout(() => {
					e.target.dispatchEvent(new PointerEvent("pointercancel", { bubbles: !0 })), l(e.target, "click", (e) => e.preventDefault(), { once: !0 }), R(e.target).activeElement !== e.target && _t(e.target), a && a({
						...e,
						type: "longpress"
					}), c.current = void 0;
				}, o), e.pointerType === "touch" && l(e.target, "contextmenu", (e) => e.preventDefault(), { once: !0 });
				let t = St(e.target);
				l(t, "pointerup", () => {
					setTimeout(() => {
						u();
					}, 100);
				}, { once: !0 });
			}
		},
		onPressEnd(e) {
			c.current && clearTimeout(c.current), i && d(e) && i({
				...e,
				type: "longpressend"
			});
		}
	});
	return { longPressProps: U(f, oo(a && !t ? s : void 0)) };
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useContextMenu.mjs
function zs(e) {
	let { onContextMenu: t } = e, n = (0, b.useRef)(!1), { longPressProps: r } = Rs({
		onLongPressStart() {
			n.current = !1;
		},
		onLongPress(e) {
			n.current ? n.current = !1 : t?.({
				target: e.target,
				x: e.x,
				y: e.y
			});
		}
	});
	return t ? { contextMenuProps: U(en() ? r : {}, {
		onContextMenu(e) {
			e.stopPropagation(), e.preventDefault(), n.current = !0;
			let r = e.currentTarget.getBoundingClientRect();
			t({
				target: e.currentTarget,
				x: e.clientX - r.x,
				y: e.clientY - r.y
			});
		},
		onKeyDown(e) {
			if (Zt() && e.ctrlKey && e.key === "Enter") {
				n.current = !1;
				let r = e.currentTarget;
				e.stopPropagation(), setTimeout(() => {
					if (n.current) n.current = !1;
					else {
						let e = r.getBoundingClientRect();
						t({
							target: r,
							x: e.width / 2,
							y: e.height / 2
						});
					}
				}, 10);
			}
		}
	}) } : { contextMenuProps: {} };
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/useCloseOnScroll.mjs
var Bs = /* @__PURE__ */ new WeakMap();
function Vs(e) {
	let { triggerRef: t, isOpen: n, onClose: r } = e;
	(0, b.useEffect)(() => !n || r === null ? void 0 : Dt(Mt(t.current), "scroll", (e) => {
		let n = B(e);
		if (!t.current || n instanceof Node && !z(n, t.current) || n instanceof HTMLInputElement || n instanceof HTMLTextAreaElement) return;
		let i = r || Bs.get(t.current);
		i && i();
	}, !0), [
		n,
		r,
		t
	]);
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/useOverlayTrigger.mjs
function Hs(e, t, n) {
	let { type: r } = e, { isOpen: i } = t;
	(0, b.useEffect)(() => {
		n && n.current && Bs.set(n.current, t.close);
	});
	let a;
	r === "menu" ? a = !0 : r === "listbox" && (a = "listbox");
	let o = sr();
	return {
		triggerProps: {
			"aria-haspopup": a,
			"aria-expanded": i,
			"aria-controls": i ? o : void 0,
			onPress: t.toggle
		},
		overlayProps: { id: o }
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/menu/useMenuTrigger.mjs
function Us(e) {
	return e && e.__esModule ? e.default : e;
}
function Ws(e, t, n) {
	let { type: r = "menu", isDisabled: i, trigger: a = "press" } = e, o = sr(), { triggerProps: s, overlayProps: c } = Hs({ type: r }, t, n), l = (e, n, r = "first") => {
		if (!e || n.isDefaultPrevented()) return !1;
		t.toggle(r);
	}, { keyboardProps: u } = Or({
		isDisabled: i,
		shortcuts: {
			Enter: (e) => l(a !== "longPress", e, "first"),
			" ": (e) => l(a !== "longPress", e, "first"),
			ArrowDown: (e) => l(a !== "longPress", e, "first"),
			ArrowUp: (e) => l(a !== "longPress", e, "last"),
			"Alt+Enter": (e) => l(a === "longPress", e, "first"),
			"Alt+ ": (e) => l(a === "longPress", e, "first"),
			"Alt+ArrowDown": (e) => l(!0, e, "first"),
			"Alt+ArrowUp": (e) => l(!0, e, "last")
		}
	}), d = Hi(Us(Is), "@react-aria/menu"), { longPressProps: f } = Rs({
		isDisabled: i || a !== "longPress",
		accessibilityDescription: d.format("longPressMessage"),
		onLongPressStart() {
			t.close();
		},
		onLongPress() {
			t.open("first");
		}
	}), p = {
		preventFocusOnPress: !0,
		onPressStart(e) {
			e.pointerType !== "touch" && e.pointerType !== "keyboard" && !i && (_t(e.target), t.open(e.pointerType === "virtual" ? "first" : null));
		},
		onPress(e) {
			e.pointerType === "touch" && !i && (_t(e.target), t.toggle());
		}
	};
	delete s.onPress;
	let { contextMenuProps: m } = zs({ onContextMenu(e) {
		let n = e.target.getBoundingClientRect();
		t.setPoint({
			x: n.x + e.x,
			y: n.y + e.y
		}), t.open();
	} });
	(0, b.useEffect)(() => {
		if (t.isOpen && a === "contextMenu") {
			let e = (e) => {
				(e.button === 2 || e.button === 0 && e.ctrlKey === !0) && B(e) === document.body && t.close();
			};
			return document.addEventListener("mousedown", e), () => document.removeEventListener("mousedown", e);
		}
	}, [t, a]);
	let h;
	if (a === "press") h = {
		...p,
		...u
	};
	else if (a === "longPress") h = {
		...f,
		...u
	};
	else if (a === "contextMenu") {
		h = m;
		let { "aria-haspopup": e, "aria-expanded": t, "aria-controls": n, ...r } = s;
		s = r;
	}
	return {
		menuTriggerProps: {
			...s,
			...h,
			id: o
		},
		menuProps: {
			...c,
			"aria-labelledby": o,
			autoFocus: t.focusStrategy || !0,
			onClose: t.close
		}
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useTypeSelect.mjs
var Gs = 1e3;
function Ks(e) {
	let { keyboardDelegate: t, selectionManager: n, onTypeSelect: r } = e, i = (0, b.useRef)({
		search: "",
		timeout: void 0
	});
	return (0, b.useEffect)(() => {
		let e = i.current.timeout;
		return () => {
			clearTimeout(e);
		};
	}, [i]), { typeSelectProps: {
		onKeyDownCapture: t.getKeyForSearch ? (e) => {
			if (i.current.search.length > 0 && e.key === " ") {
				if (e.preventDefault(), (!("continuePropagation" in e) || "continuePropagation" in e && !e.isPropagationStopped()) && e.stopPropagation(), i.current.search += " ", t.getKeyForSearch != null) {
					let e = t.getKeyForSearch(i.current.search, n.focusedKey);
					e ??= t.getKeyForSearch(i.current.search), e != null && (n.setFocusedKey(e), r && r(e));
				}
				clearTimeout(i.current.timeout), i.current.timeout = setTimeout(() => {
					i.current.search = "";
				}, Gs);
			}
		} : void 0,
		onKeyDown: t.getKeyForSearch ? (e) => {
			let a = qs(e.key);
			if (!(!a || e.ctrlKey || e.metaKey || e.altKey || !z(e.currentTarget, B(e)) || i.current.search.length === 0 && a === " ")) {
				if (i.current.search += a, t.getKeyForSearch != null) {
					let a = t.getKeyForSearch(i.current.search, n.focusedKey);
					if (a ??= t.getKeyForSearch(i.current.search), a != null) n.setFocusedKey(a), r && r(a), e.preventDefault(), "continuePropagation" in e || e.stopPropagation();
					else {
						i.current.search = "", clearTimeout(i.current.timeout), i.current.timeout = void 0;
						return;
					}
				}
				clearTimeout(i.current.timeout), i.current.timeout = setTimeout(() => {
					i.current.search = "";
				}, Gs);
			}
		} : void 0
	} };
}
function qs(e) {
	return e.length === 1 || !/^[A-Z]/i.test(e) ? e : "";
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useUpdateLayoutEffect.mjs
function Js(e, t) {
	let n = (0, b.useRef)(!0), r = (0, b.useRef)(null);
	H(() => (n.current = !0, () => {
		n.current = !1;
	}), []), H(() => {
		n.current ? n.current = !1 : (!r.current || t.some((e, t) => !Object.is(e, r[t]))) && e(), r.current = t;
	}, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useSelectableCollection.mjs
function Ys(e) {
	let { selectionManager: t, keyboardDelegate: n, ref: r, autoFocus: i = !1, shouldFocusWrap: a = !1, disallowEmptySelection: o = !1, disallowSelectAll: s = !1, escapeKeyBehavior: c = "clearSelection", selectOnFocus: l = t.selectionBehavior === "replace", disallowTypeAhead: u = !1, shouldUseVirtualFocus: d, allowsTabNavigation: f = !1, scrollRef: p = r, linkBehavior: m = "action", UNSTABLE_focusOnEntry: h } = e, { direction: g } = Oi(), _ = un(), v = (e, n, i) => {
		if (n != null) {
			if (t.isLink(n) && m === "selection" && l && !Yo(e)) {
				(0, Hr.flushSync)(() => {
					t.setFocusedKey(n, i);
				});
				let a = Xo(r, n), o = t.getItemProps(n);
				if (a) {
					_.open(a, e, o.href, o.routerOptions);
					return;
				}
				return !1;
			}
			if (t.setFocusedKey(n, i), t.isLink(n) && m === "override") return !1;
			if (e.shiftKey && t.selectionMode === "multiple") {
				t.extendSelection(n);
				return;
			}
			if (l && !Yo(e)) {
				t.replaceSelection(n);
				return;
			}
		}
		return !1;
	}, y = (e) => {
		if (n.getKeyBelow) {
			let r = t.focusedKey == null ? n.getFirstKey?.() : n.getKeyBelow?.(t.focusedKey);
			if (r == null && a && (r = n.getFirstKey?.(t.focusedKey)), r != null) {
				v(e, r);
				return;
			}
		}
		return !1;
	}, x = (e) => {
		if (n.getKeyAbove) {
			let r = t.focusedKey == null ? n.getLastKey?.() : n.getKeyAbove?.(t.focusedKey);
			if (r == null && a && (r = n.getLastKey?.(t.focusedKey)), r != null) {
				v(e, r);
				return;
			}
		}
		return !1;
	}, S = (e) => {
		if (n.getFirstKey) {
			if (t.focusedKey === null && e.shiftKey) return !1;
			let r = n.getFirstKey(t.focusedKey, di(e));
			if (t.setFocusedKey(r), r != null) {
				if (di(e) && e.shiftKey && t.selectionMode === "multiple") {
					t.extendSelection(r);
					return;
				}
				if (l) {
					t.replaceSelection(r);
					return;
				}
			}
		}
		return !1;
	}, C = (e) => {
		if (n.getKeyLeftOf) {
			let r = t.focusedKey == null ? n.getFirstKey?.() : n.getKeyLeftOf?.(t.focusedKey);
			if (r == null && a && (r = g === "rtl" ? n.getFirstKey?.(t.focusedKey) : n.getLastKey?.(t.focusedKey)), r != null) {
				v(e, r, g === "rtl" ? "first" : "last");
				return;
			}
		}
		return !1;
	}, w = (e) => {
		if (n.getKeyRightOf) {
			let r = t.focusedKey == null ? n.getFirstKey?.() : n.getKeyRightOf?.(t.focusedKey);
			if (r == null && a && (r = g === "rtl" ? n.getLastKey?.(t.focusedKey) : n.getFirstKey?.(t.focusedKey)), r != null) {
				v(e, r, g === "rtl" ? "last" : "first");
				return;
			}
		}
		return !1;
	}, T = (e) => {
		if (n.getLastKey) {
			if (t.focusedKey === null && e.shiftKey) return !1;
			let r = n.getLastKey(t.focusedKey, di(e));
			if (t.setFocusedKey(r), r != null) {
				if (di(e) && e.shiftKey && t.selectionMode === "multiple") {
					t.extendSelection(r);
					return;
				}
				if (l) {
					t.replaceSelection(r);
					return;
				}
			}
		}
		return !1;
	}, E = (e) => {
		if (n.getKeyPageBelow && t.focusedKey != null) {
			let r = n.getKeyPageBelow(t.focusedKey);
			if (r != null) return v(e, r);
		}
		return !1;
	}, D = (e) => {
		if (n.getKeyPageAbove && t.focusedKey != null) {
			let r = n.getKeyPageAbove(t.focusedKey);
			if (r != null) return v(e, r);
		}
		return !1;
	}, O = () => {
		if (t.selectionMode === "multiple" && s !== !0) {
			t.selectAll();
			return;
		}
		return !1;
	}, k = () => {
		if (c === "clearSelection" && !o && t.selectedKeys.size !== 0) {
			t.clearSelection();
			return;
		}
		return !1;
	}, A = () => {
		if (!f && r.current) {
			let e = Wa(r.current, { tabbable: !0 }), t, n;
			do
				n = e.lastChild(), n && (t = n);
			while (n);
			let i = jt();
			t && (!Nt(t) || i && !V(i)) && _t(t);
		}
		return {
			shouldContinuePropagation: !0,
			shouldPreventDefault: !1
		};
	}, j = () => (!f && r.current && r.current.focus(), {
		shouldContinuePropagation: !0,
		shouldPreventDefault: !1
	}), M = (e, t) => ({
		[Zt() ? e + "+Shift+Alt" : e + "+Shift+Control"]: t,
		[e + "+Shift"]: t,
		[Zt() ? e + "+Alt" : e + "+Control"]: t,
		[e]: t
	}), { keyboardProps: N } = Or({
		shortcuts: {
			...M("ArrowDown", y),
			...M("ArrowUp", x),
			...M("ArrowLeft", C),
			...M("ArrowRight", w),
			...M("PageDown", E),
			...M("PageUp", D)
		},
		allowRepeats: !0
	}), { keyboardProps: ee } = Or({ shortcuts: {
		...M("Home", S),
		...M("End", T),
		"Mod+A": O,
		Escape: k,
		Tab: A,
		"Tab+Shift": j
	} }), te = (0, b.useRef)({
		top: 0,
		left: 0
	});
	gi(p, "scroll", () => {
		te.current = {
			top: p.current?.scrollTop ?? 0,
			left: p.current?.scrollLeft ?? 0
		};
	});
	let P = (e) => {
		if (t.isFocused) {
			z(e.currentTarget, B(e)) || t.setFocused(!1);
			return;
		}
		if (!z(e.currentTarget, B(e))) return;
		let i = Wn();
		t.setFocused(!0);
		let a = (e) => {
			e != null && (t.setFocusedKey(e), l && !t.isSelected(e) && t.replaceSelection(e));
		};
		if (h && (i === "keyboard" || i === "virtual")) a(h === "first" ? n.getFirstKey?.() : n.getLastKey?.());
		else if (t.focusedKey == null) {
			let r = e.relatedTarget;
			r && e.currentTarget.compareDocumentPosition(r) & Node.DOCUMENT_POSITION_FOLLOWING ? a(t.lastSelectedKey ?? n.getLastKey?.()) : a(t.firstSelectedKey ?? n.getFirstKey?.());
		} else p.current && (p.current.scrollTop = te.current.top, p.current.scrollLeft = te.current.left);
		if (t.focusedKey != null && p.current) {
			let e = Xo(r, t.focusedKey);
			e instanceof HTMLElement && (!Nt(e) && !d && _t(e), (i === "keyboard" || h && i === "virtual") && ro(e, { containingElement: r.current }));
		}
	}, ne = (e) => {
		z(e.currentTarget, e.relatedTarget) || t.setFocused(!1);
	}, F = (0, b.useRef)(!1);
	gi(r, oi, d ? (e) => {
		let { detail: n } = e;
		e.stopPropagation(), t.setFocused(!0), n?.focusStrategy === "first" && (F.current = !0);
	} : void 0);
	let re = n.getFirstKey?.() ?? null;
	Js(() => {
		if (F.current) {
			if (re == null) {
				let e = jt();
				si(r.current), li(e, null), t.collection.size > 0 && (F.current = !1);
			} else t.setFocusedKey(re), F.current = !1;
		}
	}, [re, t.collection.size]), Js(() => {
		t.collection.size > 0 && (F.current = !1);
	}, [t.focusedKey]), gi(r, ai, d ? (e) => {
		e.stopPropagation(), t.setFocused(!1), e.detail?.clearFocusKey && t.setFocusedKey(null);
	} : void 0);
	let ie = (0, b.useRef)(i), ae = (0, b.useRef)(!1);
	(0, b.useEffect)(() => {
		if (ie.current) {
			let e = null;
			i === "first" && (e = n.getFirstKey?.() ?? null), i === "last" && (e = n.getLastKey?.() ?? null);
			let a = t.selectedKeys;
			if (a.size) {
				for (let n of a) if (t.canSelectItem(n)) {
					e = n;
					break;
				}
			}
			t.setFocused(!0), t.setFocusedKey(e), e != null && l && !a.size && t.canSelectItem(e) && t.replaceSelection(e), e == null && !d && r.current && er(r.current), t.collection.size > 0 && (ie.current = !1, ae.current = !0);
		}
	});
	let oe = (0, b.useRef)(t.focusedKey), se = (0, b.useRef)(null);
	(0, b.useEffect)(() => {
		if (t.isFocused && t.focusedKey != null && (t.focusedKey !== oe.current || ae.current) && p.current && r.current) {
			let e = Wn(), n = Xo(r, t.focusedKey);
			if (!(n instanceof HTMLElement)) return;
			(e === "keyboard" || ae.current) && (se.current && cancelAnimationFrame(se.current), se.current = requestAnimationFrame(() => {
				p.current && (to(p.current, n), e !== "virtual" && ro(n, { containingElement: r.current }));
			}));
		}
		!d && t.isFocused && t.focusedKey == null && oe.current != null && r.current && er(r.current), oe.current = t.focusedKey, ae.current = !1;
	}), (0, b.useEffect)(() => () => {
		se.current && cancelAnimationFrame(se.current);
	}, []), gi(r, "react-aria-focus-scope-restore", (e) => {
		e.preventDefault(), t.setFocused(!0);
	});
	let ce = {
		...U(ee, N),
		onFocus: P,
		onBlur: ne,
		onMouseDown(e) {
			p.current === B(e) && e.preventDefault();
		}
	}, { typeSelectProps: le } = Ks({
		keyboardDelegate: n,
		selectionManager: t
	});
	u || (ce = U(le, ce));
	let ue;
	d || (ue = t.focusedKey == null ? 0 : -1);
	let de = Qo(t.collection);
	return { collectionProps: U(ce, {
		tabIndex: ue,
		"data-collection": de
	}) };
}
//#endregion
//#region node_modules/react-stately/dist/private/collections/getChildNodes.mjs
function Xs(e, t) {
	return typeof t.getChildren == "function" ? t.getChildren(e.key) : e.childNodes;
}
function Zs(e) {
	return Qs(e, 0);
}
function Qs(e, t) {
	if (t < 0) return;
	let n = 0;
	for (let r of e) {
		if (n === t) return r;
		n++;
	}
}
function $s(e, t, n) {
	if (t.parentKey === n.parentKey) return t.index - n.index;
	let r = [...ec(e, t), t], i = [...ec(e, n), n], a = r.slice(0, i.length).findIndex((e, t) => e !== i[t]);
	return a === -1 ? r.findIndex((e) => e === n) >= 0 ? 1 : (i.findIndex((e) => e === t), -1) : (t = r[a], n = i[a], t.index - n.index);
}
function ec(e, t) {
	let n = [], r = t;
	for (; r?.parentKey != null;) r = e.getItem(r.parentKey), r && n.unshift(r);
	return n;
}
//#endregion
//#region node_modules/react-stately/dist/private/collections/getItemCount.mjs
var tc = /* @__PURE__ */ new WeakMap();
function nc(e) {
	let t = tc.get(e);
	if (t != null) return t;
	let n = 0, r = (t) => {
		for (let i of t) i.type === "section" ? r(Xs(i, e)) : i.type === "item" && n++;
	};
	return r(e), tc.set(e, n), n;
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/useCollator.mjs
var rc = /* @__PURE__ */ new Map();
function ic(e) {
	let { locale: t } = Oi(), n = t + (e ? Object.entries(e).sort((e, t) => e[0] < t[0] ? -1 : 1).join() : "");
	if (rc.has(n)) return rc.get(n);
	let r = new Intl.Collator(t, e);
	return rc.set(n, r), r;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/PressResponder.mjs
function ac({ children: e }) {
	let t = (0, b.useMemo)(() => ({ register: () => {} }), []);
	return /*#__PURE__*/ b.createElement(ra.Provider, { value: t }, e);
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/PortalProvider.mjs
var oc = /*#__PURE__*/ (0, b.createContext)({});
function sc(e) {
	let { getContainer: t } = e, { getContainer: n } = cc();
	return /*#__PURE__*/ b.createElement(oc.Provider, { value: { getContainer: t === null ? void 0 : t ?? n } }, e.children);
}
function cc() {
	return (0, b.useContext)(oc) ?? {};
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/Overlay.mjs
var lc = /*#__PURE__*/ b.createContext(null);
function uc(e) {
	let t = En(), { portalContainer: n = t ? null : document.body, isExiting: r } = e, [i, a] = (0, b.useState)(!1), o = (0, b.useMemo)(() => ({
		contain: i,
		setContain: a
	}), [i, a]), { getContainer: s } = cc();
	if (!e.portalContainer && s && (n = s()), !n) return null;
	let c = e.children;
	return e.disableFocusManagement || (c = /*#__PURE__*/ b.createElement(wa, {
		restoreFocus: !0,
		contain: (e.shouldContainFocus || i) && !r
	}, c)), c = /*#__PURE__*/ b.createElement(lc.Provider, { value: o }, /*#__PURE__*/ b.createElement(ac, null, /*#__PURE__*/ b.createElement(jr.Provider, { value: null }, c))), /*#__PURE__*/ Hr.createPortal(c, n);
}
function dc() {
	let e = (0, b.useContext)(lc)?.setContain;
	H(() => {
		e?.(!0);
	}, [e]);
}
//#endregion
//#region node_modules/react-aria/dist/private/dialog/useDialog.mjs
function fc(e, t) {
	let { role: n = "dialog" } = e, r = lr();
	r = e["aria-label"] ? void 0 : r;
	let i = lr();
	i = n === "alertdialog" && !e["aria-describedby"] ? i : void 0;
	let a = (0, b.useRef)(!1);
	(0, b.useEffect)(() => {
		if (t.current && !Nt(t.current)) {
			er(t.current);
			let e = setTimeout(() => {
				(jt() === t.current || jt() === document.body) && (a.current = !0, t.current && (t.current.blur(), er(t.current)), a.current = !1);
			}, 500);
			return () => {
				clearTimeout(e);
			};
		}
	}, [t]), dc(), (0, b.useRef)(!1), (0, b.useEffect)(() => {});
	let o = e["aria-describedby"] ?? i;
	return {
		dialogProps: {
			...Yi(e, { labelable: !0 }),
			role: n,
			tabIndex: -1,
			"aria-labelledby": e["aria-labelledby"] ?? r,
			"aria-describedby": o,
			onBlur: (e) => {
				a.current && e.stopPropagation();
			}
		},
		titleProps: { id: r },
		contentProps: { id: i }
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/focus/useFocusRing.mjs
function pc(e = {}) {
	let { autoFocus: t = !1, isTextInput: n, within: r } = e, i = (0, b.useRef)({
		isFocused: !1,
		isFocusVisible: t || Un()
	}), [a, o] = (0, b.useState)(!1), [s, c] = (0, b.useState)(() => i.current.isFocused && i.current.isFocusVisible), l = (0, b.useCallback)(() => c(i.current.isFocused && i.current.isFocusVisible), []), u = (0, b.useCallback)((e) => {
		i.current.isFocused = e, i.current.isFocusVisible = Un(), o(e), l();
	}, [l]);
	Jn((e) => {
		i.current.isFocusVisible = e, l();
	}, [n, a], {
		enabled: a,
		isTextInput: n
	});
	let { focusProps: d } = mr({
		isDisabled: r,
		onFocusChange: u
	}), { focusWithinProps: f } = jo({
		isDisabled: !r,
		onFocusWithinChange: u
	});
	return {
		isFocused: a,
		isFocusVisible: s,
		focusProps: r ? f : d
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/useListFormatter.mjs
function mc(e = {}) {
	let { locale: t } = Oi();
	return (0, b.useMemo)(() => new Intl.ListFormat(t, e), [t, e]);
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useHover.mjs
var hc = !1, gc = 0;
function _c() {
	hc = !0, setTimeout(() => {
		hc = !1;
	}, 500);
}
function vc(e) {
	e.pointerType === "touch" && _c();
}
function yc() {
	let e = R(null);
	if (e !== void 0) return gc === 0 && typeof PointerEvent < "u" && e.addEventListener("pointerup", vc), gc++, () => {
		gc--, !(gc > 0) && typeof PointerEvent < "u" && e.removeEventListener("pointerup", vc);
	};
}
function bc(e) {
	let { onHoverStart: t, onHoverChange: n, onHoverEnd: r, isDisabled: i } = e, [a, o] = (0, b.useState)(!1), s = (0, b.useRef)({
		isHovered: !1,
		ignoreEmulatedMouseEvents: !1,
		pointerType: "",
		target: null
	}).current;
	(0, b.useEffect)(yc, []);
	let { addGlobalListener: c, removeAllGlobalListeners: l } = ia(), { hoverProps: u, triggerHoverEnd: d } = (0, b.useMemo)(() => {
		let e = (e, r) => {
			if (s.pointerType = r, i || r === "touch" || s.isHovered || !z(e.currentTarget, B(e))) return;
			s.isHovered = !0;
			let l = e.currentTarget;
			s.target = l, c(R(B(e)), "pointerover", (e) => {
				s.isHovered && s.target && !z(s.target, B(e)) && a(e, e.pointerType);
			}, { capture: !0 }), t && t({
				type: "hoverstart",
				target: l,
				pointerType: r
			}), n && n(!0), o(!0);
		}, a = (e, t) => {
			let i = s.target;
			s.pointerType = "", s.target = null, !(t === "touch" || !s.isHovered || !i) && (s.isHovered = !1, l(), r && r({
				type: "hoverend",
				target: i,
				pointerType: t
			}), n && n(!1), o(!1));
		}, u = {};
		return typeof PointerEvent < "u" && (u.onPointerEnter = (t) => {
			hc && t.pointerType === "mouse" || e(t, t.pointerType);
		}, u.onPointerLeave = (e) => {
			!i && z(e.currentTarget, B(e)) && a(e, e.pointerType);
		}), {
			hoverProps: u,
			triggerHoverEnd: a
		};
	}, [
		t,
		n,
		r,
		i,
		s,
		c,
		l
	]);
	return (0, b.useEffect)(() => {
		i && d({ currentTarget: s.target }, s.pointerType);
	}, [i]), {
		hoverProps: u,
		isHovered: a
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useInteractOutside.mjs
function xc(e) {
	let { ref: t, onInteractOutside: n, isDisabled: r, onInteractOutsideStart: i } = e, a = (0, b.useRef)({
		isPointerDown: !1,
		ignoreEmulatedMouseEvents: !1
	}), o = hi((e) => {
		n && Sc(e, t) && (i && i(e), a.current.isPointerDown = !0);
	}), s = hi((e) => {
		n && n(e);
	});
	(0, b.useEffect)(() => {
		let e = a.current;
		if (r) return;
		let n = t.current, i = R(n);
		if (typeof PointerEvent < "u") {
			let n = (n) => {
				e.isPointerDown && Sc(n, t) && s(n), e.isPointerDown = !1;
			};
			return i.addEventListener("pointerdown", o, !0), i.addEventListener("click", n, !0), () => {
				i.removeEventListener("pointerdown", o, !0), i.removeEventListener("click", n, !0);
			};
		}
	}, [t, r]);
}
function Sc(e, t) {
	if (e.button > 0) return !1;
	let n = B(e);
	if (n) {
		let e = n.ownerDocument;
		if (!e || !z(e.documentElement, n) || n.closest("[data-react-aria-top-layer]")) return !1;
	}
	return t.current ? !e.composedPath().includes(t.current) : !1;
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useSelectableList.mjs
function Cc(e) {
	let { selectionManager: t, collection: n, disabledKeys: r, ref: i, keyboardDelegate: a, layoutDelegate: o, orientation: s } = e, c = ic({
		usage: "search",
		sensitivity: "base"
	}), l = t.disabledBehavior, u = (0, b.useMemo)(() => a || new ts({
		collection: n,
		disabledKeys: r,
		disabledBehavior: l,
		ref: i,
		collator: c,
		layoutDelegate: o,
		orientation: s
	}), [
		a,
		o,
		n,
		r,
		i,
		c,
		l,
		s
	]), { collectionProps: d } = Ys({
		...e,
		ref: i,
		selectionManager: t,
		keyboardDelegate: u
	});
	return { listProps: d };
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useSelectableItem.mjs
function wc(e) {
	let { id: t, selectionManager: n, key: r, ref: i, shouldSelectOnPressUp: a, shouldUseVirtualFocus: o, focus: s, isDisabled: c, onAction: l, allowsDifferentPressOrigin: u, linkBehavior: d = "action" } = e, f = un();
	t = sr(t);
	let p = (e) => {
		if (e.pointerType === "keyboard" && Yo(e)) n.toggleSelection(r);
		else {
			if (n.selectionMode === "none") return;
			if (n.isLink(r)) {
				if (d === "selection" && i.current) {
					let t = n.getItemProps(r);
					f.open(i.current, e, t.href, t.routerOptions), n.setSelectedKeys(n.selectedKeys);
					return;
				}
				if (d === "override" || d === "none") return;
			}
			n.selectionMode === "single" ? n.isSelected(r) && !n.disallowEmptySelection ? n.toggleSelection(r) : n.replaceSelection(r) : e && e.shiftKey ? n.extendSelection(r) : n.selectionBehavior === "toggle" || e && (di(e) || e.pointerType === "touch" || e.pointerType === "virtual") ? n.toggleSelection(r) : n.replaceSelection(r);
		}
	};
	(0, b.useEffect)(() => {
		r === n.focusedKey && n.isFocused && (o ? si(i.current) : s ? s() : jt() !== i.current && i.current && er(i.current));
	}, [
		i,
		r,
		n.focusedKey,
		n.childFocusStrategy,
		n.isFocused,
		o
	]), c ||= n.isDisabled(r);
	let m = {};
	!o && !c ? m = {
		tabIndex: r === n.focusedKey ? 0 : -1,
		onFocus(e) {
			B(e) === i.current && n.setFocusedKey(r);
		}
	} : c && (m.onMouseDown = (e) => {
		e.preventDefault();
	}), (0, b.useEffect)(() => {
		c && n.focusedKey === r && n.setFocusedKey(null);
	}, [
		n,
		c,
		r
	]);
	let h = n.isLink(r) && d === "override", g = l && e.UNSTABLE_itemBehavior === "action", _ = n.isLink(r) && d !== "selection" && d !== "none", v = !c && n.canSelectItem(r) && !h && !g, y = (l || _) && !c, x = y && (n.selectionBehavior === "replace" ? !v : !v || n.isEmpty), S = y && v && n.selectionBehavior === "replace", C = x || S, w = (0, b.useRef)(null), T = C && v, E = (0, b.useRef)(!1), D = (0, b.useRef)(!1), O = n.getItemProps(r), k = (e) => {
		l && (l(), i.current?.dispatchEvent(new CustomEvent("react-aria-item-action", { bubbles: !0 }))), _ && i.current && f.open(i.current, e, O.href, O.routerOptions);
	}, A = { ref: i };
	a ? (A.onPressStart = (e) => {
		w.current = e.pointerType, E.current = T, e.pointerType === "keyboard" && (!C || Ec(e.key)) && p(e);
	}, u ? (A.onPressUp = x ? void 0 : (e) => {
		e.pointerType === "mouse" && v && p(e);
	}, A.onPress = x ? k : (e) => {
		e.pointerType !== "keyboard" && e.pointerType !== "mouse" && v && p(e);
	}) : A.onPress = (e) => {
		if (x || S && e.pointerType !== "mouse") {
			if (e.pointerType === "keyboard" && !Tc(e.key)) return;
			k(e);
		} else e.pointerType !== "keyboard" && v && p(e);
	}) : (A.onPressStart = (e) => {
		w.current = e.pointerType, E.current = T, D.current = x, v && (e.pointerType === "mouse" && !x || e.pointerType === "keyboard" && (!y || Ec(e.key))) && p(e);
	}, A.onPress = (e) => {
		(e.pointerType === "touch" || e.pointerType === "pen" || e.pointerType === "virtual" || e.pointerType === "keyboard" && C && Tc(e.key) || e.pointerType === "mouse" && D.current) && (C ? k(e) : v && p(e));
	});
	let j = $o(n.collection);
	if (m["data-collection"] = j, m["data-key"] = r, A.preventFocusOnPress = o, o && (A = U(A, {
		onPressStart(e) {
			e.pointerType !== "touch" && (n.setFocused(!0), n.setFocusedKey(r));
		},
		onPress(e) {
			e.pointerType === "touch" && (n.setFocused(!0), n.setFocusedKey(r));
		}
	})), O) for (let e of [
		"onPressStart",
		"onPressEnd",
		"onPressChange",
		"onPress",
		"onPressUp",
		"onClick"
	]) O[e] && (A[e] = tr(A[e], O[e]));
	let { pressProps: M, isPressed: N } = ua(A), ee = S ? (e) => {
		w.current === "mouse" && (e.stopPropagation(), e.preventDefault(), k(e));
	} : void 0, { longPressProps: te } = Rs({
		isDisabled: !T,
		onLongPress(e) {
			e.pointerType === "touch" && (p(e), n.setSelectionBehavior("toggle"));
		}
	}), P = (e) => {
		w.current === "touch" && E.current && e.preventDefault();
	}, ne = d !== "none" && n.isLink(r) ? (e) => {
		dn.isOpening || e.preventDefault();
	} : void 0, F = U(m, v || x || o && !c ? M : {}, T ? te : {}, {
		onDoubleClick: ee,
		onDragStartCapture: P,
		onClick: ne,
		id: t
	}, o ? { onMouseDown: (e) => e.preventDefault() } : void 0), re = (e) => {
		let t = e;
		for (; t && t !== i.current;) {
			let e = t.getAttribute("data-collection");
			if (e != null) return e !== j;
			t = t.parentElement;
		}
		return V(e);
	}, ie = F.onPointerDown;
	F.onPointerDown = (e) => {
		let t = B(e);
		if (t && t !== i.current && re(t)) {
			e.stopPropagation();
			return;
		}
		ie?.(e);
	};
	let ae = F.onMouseDown;
	return F.onMouseDown = (e) => {
		let t = B(e);
		if (t && t !== i.current && re(t)) {
			e.stopPropagation();
			return;
		}
		ae?.(e);
	}, {
		itemProps: F,
		isPressed: N,
		isSelected: n.isSelected(r),
		isFocused: n.isFocused && n.focusedKey === r,
		isDisabled: c,
		allowsSelection: v,
		hasAction: C
	};
}
function Tc(e) {
	return e === "Enter";
}
function Ec(e) {
	return e === " ";
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/useListBox.mjs
function Dc(e, t, n) {
	let r = Yi(e, { labelable: !0 }), i = e.selectionBehavior || "toggle", a = e.orientation || "vertical", o = e.linkBehavior || (i === "replace" ? "action" : "override");
	i === "toggle" && o === "action" && (o = "override");
	let { listProps: s } = Cc({
		...e,
		ref: n,
		selectionManager: t.selectionManager,
		collection: t.collection,
		disabledKeys: t.disabledKeys,
		linkBehavior: o
	}), { focusWithinProps: c } = jo({
		onFocusWithin: e.onFocus,
		onBlurWithin: e.onBlur,
		onFocusWithinChange: e.onFocusChange
	}), l = sr(e.id);
	Ko.set(t, {
		id: l,
		shouldUseVirtualFocus: e.shouldUseVirtualFocus,
		shouldSelectOnPressUp: e.shouldSelectOnPressUp,
		shouldFocusOnHover: e.shouldFocusOnHover,
		isVirtualized: e.isVirtualized,
		onAction: e.onAction,
		linkBehavior: o,
		UNSTABLE_itemBehavior: e.UNSTABLE_itemBehavior
	});
	let { labelProps: u, fieldProps: d } = ko({
		...e,
		id: l,
		labelElementType: "span"
	});
	return {
		labelProps: u,
		listBoxProps: U(r, c, t.selectionManager.selectionMode === "multiple" ? { "aria-multiselectable": "true" } : {}, {
			role: "listbox",
			"aria-orientation": a,
			...U(d, s)
		})
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/useListBoxSection.mjs
function Oc(e) {
	let { heading: t, "aria-label": n } = e, r = sr();
	return {
		itemProps: { role: "presentation" },
		headingProps: t ? {
			id: r,
			role: "presentation",
			onMouseDown: (e) => {
				e.preventDefault();
			}
		} : {},
		groupProps: {
			role: "group",
			"aria-label": n,
			"aria-labelledby": t ? r : void 0
		}
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/useOption.mjs
function kc(e, t, n) {
	let { key: r } = e, i = Ko.get(t), a = e.isDisabled ?? t.selectionManager.isDisabled(r), o = e.isSelected ?? t.selectionManager.isSelected(r), s = e.shouldSelectOnPressUp ?? i?.shouldSelectOnPressUp, c = e.shouldFocusOnHover ?? i?.shouldFocusOnHover, l = e.shouldUseVirtualFocus ?? i?.shouldUseVirtualFocus, u = e.isVirtualized ?? i?.isVirtualized, d = lr(), f = lr(), p = {
		role: "option",
		"aria-disabled": a || void 0,
		"aria-selected": t.selectionManager.selectionMode === "none" ? void 0 : o,
		"aria-label": e["aria-label"],
		"aria-labelledby": d,
		"aria-describedby": f
	}, m = t.collection.getItem(r);
	if (u) {
		let e = Number(m?.index);
		p["aria-posinset"] = Number.isNaN(e) ? void 0 : e + 1, p["aria-setsize"] = nc(t.collection);
	}
	let h = i?.onAction ? () => i?.onAction?.(r) : void 0, g = Jo(t, r), { itemProps: _, isPressed: v, isFocused: y, hasAction: b, allowsSelection: x } = wc({
		selectionManager: t.selectionManager,
		key: r,
		ref: n,
		shouldSelectOnPressUp: s,
		allowsDifferentPressOrigin: s && c,
		isVirtualized: u,
		shouldUseVirtualFocus: l,
		isDisabled: a,
		onAction: h || m?.props?.onAction ? tr(m?.props?.onAction, h) : void 0,
		linkBehavior: i?.linkBehavior,
		UNSTABLE_itemBehavior: i?.UNSTABLE_itemBehavior,
		id: g
	}), { hoverProps: S } = bc({
		isDisabled: a || !c,
		onHoverStart() {
			Un() || (t.selectionManager.setFocused(!0), t.selectionManager.setFocusedKey(r));
		}
	}), C = Yi(m?.props);
	delete C.id;
	let w = mn(m?.props);
	return {
		optionProps: {
			...p,
			...U(C, _, S, w),
			id: g
		},
		labelProps: { id: d },
		descriptionProps: { id: f },
		isFocused: y,
		isFocusVisible: y && t.selectionManager.isFocused && Un(),
		isSelected: o,
		isDisabled: a,
		isPressed: v,
		allowsSelection: x,
		hasAction: b
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useResizeObserver.mjs
function Ac() {
	return window.ResizeObserver !== void 0;
}
function jc(e) {
	let { ref: t, box: n, onResize: r } = e, i = hi(r);
	(0, b.useEffect)(() => {
		let e = t?.current;
		if (e) {
			if (Ac()) {
				let t = new window.ResizeObserver((e) => {
					e.length && i();
				});
				return t.observe(e, { box: n }), () => {
					e && t.unobserve(e);
				};
			}
			return window.addEventListener("resize", i, !1), () => {
				window.removeEventListener("resize", i, !1);
			};
		}
	}, [t, n]);
}
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ar-AE.mjs
var Mc = {};
Mc = { dismiss: "تجاهل" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/bg-BG.mjs
var Nc = {};
Nc = { dismiss: "Отхвърляне" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/cs-CZ.mjs
var Pc = {};
Pc = { dismiss: "Odstranit" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/da-DK.mjs
var Fc = {};
Fc = { dismiss: "Luk" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/de-DE.mjs
var Ic = {};
Ic = { dismiss: "Schließen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/el-GR.mjs
var Lc = {};
Lc = { dismiss: "Απόρριψη" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/en-US.mjs
var Rc = {};
Rc = { dismiss: "Dismiss" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/es-ES.mjs
var zc = {};
zc = { dismiss: "Descartar" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/et-EE.mjs
var Bc = {};
Bc = { dismiss: "Lõpeta" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/fi-FI.mjs
var Vc = {};
Vc = { dismiss: "Hylkää" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/fr-FR.mjs
var Hc = {};
Hc = { dismiss: "Rejeter" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/he-IL.mjs
var Uc = {};
Uc = { dismiss: "התעלם" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/hr-HR.mjs
var Wc = {};
Wc = { dismiss: "Odbaci" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/hu-HU.mjs
var Gc = {};
Gc = { dismiss: "Elutasítás" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/it-IT.mjs
var Kc = {};
Kc = { dismiss: "Ignora" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ja-JP.mjs
var qc = {};
qc = { dismiss: "閉じる" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ko-KR.mjs
var Jc = {};
Jc = { dismiss: "무시" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/lt-LT.mjs
var Yc = {};
Yc = { dismiss: "Atmesti" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/lv-LV.mjs
var Xc = {};
Xc = { dismiss: "Nerādīt" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/nb-NO.mjs
var Zc = {};
Zc = { dismiss: "Lukk" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/nl-NL.mjs
var Qc = {};
Qc = { dismiss: "Negeren" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/pl-PL.mjs
var $c = {};
$c = { dismiss: "Zignoruj" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/pt-BR.mjs
var el = {};
el = { dismiss: "Descartar" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/pt-PT.mjs
var tl = {};
tl = { dismiss: "Dispensar" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ro-RO.mjs
var nl = {};
nl = { dismiss: "Revocare" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ru-RU.mjs
var rl = {};
rl = { dismiss: "Пропустить" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sk-SK.mjs
var il = {};
il = { dismiss: "Zrušiť" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sl-SI.mjs
var al = {};
al = { dismiss: "Opusti" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sr-SP.mjs
var ol = {};
ol = { dismiss: "Odbaci" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sv-SE.mjs
var sl = {};
sl = { dismiss: "Avvisa" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/tr-TR.mjs
var cl = {};
cl = { dismiss: "Kapat" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/uk-UA.mjs
var ll = {};
ll = { dismiss: "Скасувати" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/zh-CN.mjs
var ul = {};
ul = { dismiss: "取消" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/zh-TW.mjs
var dl = {};
dl = { dismiss: "關閉" };
//#endregion
//#region node_modules/react-aria/dist/private/overlays/intlStrings.mjs
var fl = {};
fl = {
	"ar-AE": Mc,
	"bg-BG": Nc,
	"cs-CZ": Pc,
	"da-DK": Fc,
	"de-DE": Ic,
	"el-GR": Lc,
	"en-US": Rc,
	"es-ES": zc,
	"et-EE": Bc,
	"fi-FI": Vc,
	"fr-FR": Hc,
	"he-IL": Uc,
	"hr-HR": Wc,
	"hu-HU": Gc,
	"it-IT": Kc,
	"ja-JP": qc,
	"ko-KR": Jc,
	"lt-LT": Yc,
	"lv-LV": Xc,
	"nb-NO": Zc,
	"nl-NL": Qc,
	"pl-PL": $c,
	"pt-BR": el,
	"pt-PT": tl,
	"ro-RO": nl,
	"ru-RU": rl,
	"sk-SK": il,
	"sl-SI": al,
	"sr-SP": ol,
	"sv-SE": sl,
	"tr-TR": cl,
	"uk-UA": ll,
	"zh-CN": ul,
	"zh-TW": dl
};
//#endregion
//#region node_modules/react-aria/dist/private/overlays/DismissButton.mjs
function pl(e) {
	return e && e.__esModule ? e.default : e;
}
function ml(e) {
	let { onDismiss: t, ...n } = e, r = _i(n, Hi(pl(fl), "@react-aria/overlays").format("dismiss")), i = () => {
		t && t();
	};
	return /*#__PURE__*/ b.createElement(Ro, null, /*#__PURE__*/ b.createElement("button", {
		...r,
		tabIndex: -1,
		onClick: i,
		style: {
			width: 1,
			height: 1
		}
	}));
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/useOverlay.mjs
var K = [];
function hl(e, t) {
	let { onClose: n, shouldCloseOnBlur: r, isOpen: i, isDismissable: a = !1, isKeyboardDismissDisabled: o = !1, shouldCloseOnInteractOutside: s } = e, c = (0, b.useRef)(void 0);
	(0, b.useEffect)(() => {
		if (i && !K.includes(t)) return K.push(t), () => {
			let e = K.indexOf(t);
			e >= 0 && K.splice(e, 1);
		};
	}, [i, t]);
	let l = () => {
		K[K.length - 1] === t && n && n();
	}, u = (e) => {
		let n = K[K.length - 1];
		c.current = n, (!s || s(B(e))) && n === t && e.stopPropagation();
	}, d = (e) => {
		(!s || s(B(e))) && (K[K.length - 1] === t && e.stopPropagation(), c.current === t && l()), c.current = void 0;
	}, { keyboardProps: f } = Or({ shortcuts: { Escape: () => {
		if (!o) {
			l();
			return;
		}
		return !1;
	} } });
	xc({
		ref: t,
		onInteractOutside: a && i ? d : void 0,
		onInteractOutsideStart: u
	});
	let { focusWithinProps: p } = jo({
		isDisabled: !r,
		onBlurWithin: (e) => {
			!e.relatedTarget || Pa(e.relatedTarget) || (!s || s(e.relatedTarget)) && n?.();
		}
	});
	return {
		overlayProps: {
			...f,
			...p
		},
		underlayProps: {}
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/usePreventScroll.mjs
var gl = typeof document < "u" && window.visualViewport, _l = 0, vl;
function yl(e = {}) {
	let { isDisabled: t } = e;
	H(() => {
		if (!t) return _l++, _l === 1 && (vl = en() && nn() ? xl() : bl()), () => {
			_l--, _l === 0 && vl();
		};
	}, [t]);
}
function bl() {
	let e = window.innerWidth - document.documentElement.clientWidth;
	return tr(e > 0 && ("scrollbarGutter" in document.documentElement.style ? Ot(document.documentElement, "scrollbar-gutter", "stable") : Ot(document.documentElement, "padding-right", `${e}px`)), Ot(document.documentElement, "overflow", "hidden"));
}
function xl() {
	let e = Ot(document.documentElement, "overflow", "hidden"), t, n = !1, r = (e) => {
		let r = B(e);
		t = Qa(r) ? r : $a(r, !0), n = !1;
		let i = r.ownerDocument.defaultView.getSelection();
		i && !i.isCollapsed && i.containsNode(r, !0) && (n = !0), e.composedPath().some((e) => e instanceof HTMLInputElement && e.type === "range") && (n = !0), "selectionStart" in r && "selectionEnd" in r && r.selectionStart < r.selectionEnd && r.ownerDocument.activeElement === r && (n = !0);
	}, i = document.createElement("style"), a = na();
	a && (i.nonce = a), i.textContent = "@layer {\n  * {\n    overscroll-behavior: contain;\n  }\n}", document.head.prepend(i);
	let o = (e) => {
		if (!(e.touches.length === 2 || n)) {
			if (!t || t === document.documentElement || t === document.body) {
				e.preventDefault();
				return;
			}
			t.scrollHeight === t.clientHeight && t.scrollWidth === t.clientWidth && e.preventDefault();
		}
	}, s = (e) => {
		let t = B(e), n = e.relatedTarget;
		n && pi(n) ? (n.focus({ preventScroll: !0 }), Sl(n, pi(t))) : n || (t.parentElement?.closest("[tabindex]"))?.focus({ preventScroll: !0 });
	}, c = HTMLElement.prototype.focus;
	Reflect.defineProperty(HTMLElement.prototype, "focus", {
		configurable: !0,
		writable: !0,
		value: function(e) {
			let t = jt(), n = t != null && pi(t);
			c.call(this, {
				...e,
				preventScroll: !0
			}), (!e || !e.preventScroll) && Sl(this, n);
		}
	});
	let l = tr(Dt(document, "touchstart", r, {
		passive: !1,
		capture: !0
	}), Dt(document, "touchmove", o, {
		passive: !1,
		capture: !0
	}), Dt(document, "blur", s, !0));
	return () => {
		e(), l(), i.remove(), Reflect.defineProperty(HTMLElement.prototype, "focus", {
			configurable: !0,
			writable: !0,
			value: c
		});
	};
}
function Sl(e, t) {
	t || !gl ? Cl(e) : gl.addEventListener("resize", () => Cl(e), { once: !0 });
}
function Cl(e) {
	let t = document.scrollingElement || document.documentElement, n = e;
	for (; n && n !== t;) {
		let e = $a(n);
		if (e !== document.documentElement && e !== document.body && e !== n) {
			let t = e.getBoundingClientRect(), r = n.getBoundingClientRect();
			if (r.top < t.top || r.bottom > t.top + n.clientHeight) {
				let n = t.bottom;
				gl && (n = Math.min(n, gl.offsetTop + gl.height));
				let i = r.top - t.top - ((n - t.top) / 2 - r.height / 2);
				e.scrollTo({
					top: Math.max(0, Math.min(e.scrollHeight - e.clientHeight, e.scrollTop + i)),
					behavior: "smooth"
				});
			}
		}
		n = e.parentElement;
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/calculatePosition.mjs
var wl = {
	top: "top",
	bottom: "top",
	left: "left",
	right: "left"
}, Tl = {
	top: "bottom",
	bottom: "top",
	left: "right",
	right: "left"
}, El = {
	top: "left",
	left: "top"
}, Dl = {
	top: "height",
	left: "width"
}, Ol = {
	width: "totalWidth",
	height: "totalHeight"
}, kl = {}, Al = () => typeof document < "u" ? window.visualViewport : null;
function jl(e, t) {
	let n = 0, r = 0, i = 0, a = 0, o = 0, s = 0, c = {}, l = (t?.scale ?? 1) > 1;
	if (e.tagName === "BODY" || e.tagName === "HTML") {
		let l = document.documentElement;
		i = l.clientWidth, a = l.clientHeight, n = t?.width ?? i, r = t?.height ?? a, c.top = l.scrollTop || e.scrollTop, c.left = l.scrollLeft || e.scrollLeft, t && (o = Math.max(0, t.pageTop - (c.top ?? 0)), s = Math.max(0, t.pageLeft - (c.left ?? 0)));
	} else ({width: n, height: r, top: o, left: s} = Hl(e, !1)), c.top = e.scrollTop, c.left = e.scrollLeft, i = n, a = r;
	return nn() && (e.tagName === "BODY" || e.tagName === "HTML") && l && (c.top = 0, c.left = 0, o = t?.pageTop ?? 0, s = t?.pageLeft ?? 0), {
		width: n,
		height: r,
		totalWidth: i,
		totalHeight: a,
		scroll: c,
		top: o,
		left: s
	};
}
function Ml(e) {
	return {
		top: e.scrollTop,
		left: e.scrollLeft,
		width: e.scrollWidth,
		height: e.scrollHeight
	};
}
function Nl(e, t, n, r, i, a, o) {
	let s = i.scroll[e] ?? 0, c = r[Dl[e]], l = o[e] + r.scroll[wl[e]] + a, u = o[e] + r.scroll[wl[e]] + c - a, d = t - s + r.scroll[wl[e]] + o[e] - r[wl[e]], f = t - s + n + r.scroll[wl[e]] + o[e] - r[wl[e]];
	return d < l ? l - d : f > u ? Math.max(u - f, l - d) : 0;
}
function Pl(e) {
	let t = window.getComputedStyle(e);
	return {
		top: parseInt(t.marginTop, 10) || 0,
		bottom: parseInt(t.marginBottom, 10) || 0,
		left: parseInt(t.marginLeft, 10) || 0,
		right: parseInt(t.marginRight, 10) || 0
	};
}
function Fl(e) {
	if (kl[e]) return kl[e];
	let [t, n] = e.split(" "), r = wl[t] || "right", i = El[r];
	wl[n] || (n = "center");
	let a = Dl[r], o = Dl[i];
	return kl[e] = {
		placement: t,
		crossPlacement: n,
		axis: r,
		crossAxis: i,
		size: a,
		crossSize: o
	}, kl[e];
}
function Il(e, t, n, r, i, a, o, s, c, l, u) {
	let { placement: d, crossPlacement: f, axis: p, crossAxis: m, size: h, crossSize: g } = r, _ = {};
	_[m] = e[m] ?? 0, f === "center" ? _[m] += ((e[g] ?? 0) - (n[g] ?? 0)) / 2 : f !== m && (_[m] += (e[g] ?? 0) - (n[g] ?? 0)), _[m] += a;
	let v = e[m] - n[g] + c + l, y = e[m] + e[g] - c - l;
	if (_[m] = Io(_[m], v, y), d === p) {
		let t = s ? u[h] : u[Ol[h]];
		_[Tl[p]] = Math.floor(t - e[p] + i);
	} else _[p] = Math.floor(e[p] + e[h] + i);
	return _;
}
function Ll(e, t, n, r, i, a, o, s, c, l, u) {
	let d = (e.top == null ? c[Ol.height] - (e.bottom ?? 0) - o : e.top) - (c.scroll.top ?? 0), f = l ? n.top : 0, p = {
		top: Math.max(t.top + f, (u?.offsetTop ?? t.top) + f),
		bottom: Math.min(t.top + t.height + f, (u?.offsetTop ?? 0) + (u?.height ?? 0))
	};
	return s === "top" ? Math.max(0, d + o - p.top - ((i.top ?? 0) + (i.bottom ?? 0) + a)) : Math.max(0, p.bottom - d - ((i.top ?? 0) + (i.bottom ?? 0) + a));
}
function Rl(e, t, n, r, i, a, o, s) {
	let { placement: c, axis: l, size: u } = a;
	return c === l ? Math.max(0, n[l] - (o.scroll[l] ?? 0) - (e[l] + (s ? t[l] : 0)) - (r[l] ?? 0) - r[Tl[l]] - i) : Math.max(0, e[u] + e[l] + (s ? t[l] : 0) - n[l] - n[u] + (o.scroll[l] ?? 0) - (r[l] ?? 0) - r[Tl[l]] - i);
}
function zl(e, t, n, r, i, a, o, s, c, l, u, d, f, p, m, h, g, _) {
	let v = Fl(e), { size: y, crossAxis: b, crossSize: x, placement: S, crossPlacement: C } = v, w = Il(t, s, n, v, u, d, l, f, m, h, c), T = u, E = Rl(s, l, t, i, a + u, v, c, g);
	if (o && n[y] > E) {
		let e = Fl(`${Tl[S]} ${C}`), r = Il(t, s, n, e, u, d, l, f, m, h, c);
		Rl(s, l, t, i, a + u, e, c, g) > E && (v = e, w = r, T = u);
	}
	let D = "bottom";
	v.axis === "top" ? v.placement === "top" ? D = "top" : v.placement === "bottom" && (D = "bottom") : v.crossAxis === "top" && (v.crossPlacement === "top" ? D = "bottom" : v.crossPlacement === "bottom" && (D = "top"));
	let O = Nl(b, w[b], n[x], s, c, a, l);
	w[b] += O;
	let k = Ll(w, s, l, f, i, a, n.height, D, c, g, _);
	p && p < k && (k = p), n.height = Math.min(n.height, k), w = Il(t, s, n, v, T, d, l, f, m, h, c), O = Nl(b, w[b], n[x], s, c, a, l), w[b] += O;
	let A = {}, j = t[b] - w[b] - i[wl[b]], M = j + .5 * t[x], N = m / 2 + h, ee = wl[b] === "left" ? (i.left ?? 0) + (i.right ?? 0) : (i.top ?? 0) + (i.bottom ?? 0), te = n[x] - ee - m / 2 - h;
	A[b] = Io(Io(M, t[b] + m / 2 - (w[b] + i[wl[b]]), t[b] + t[x] - m / 2 - (w[b] + i[wl[b]])), N, te), {placement: S, crossPlacement: C} = v, m ? j = A[b] : C === "right" ? j += t[x] : C === "center" && (j += t[x] / 2);
	let P = S === "left" || S === "top" ? n[y] : 0, ne = {
		x: S === "top" || S === "bottom" ? j : P,
		y: S === "left" || S === "right" ? j : P
	};
	return {
		position: w,
		maxHeight: k,
		arrowOffsetLeft: A.left,
		arrowOffsetTop: A.top,
		placement: S,
		triggerAnchorPoint: ne
	};
}
function Bl(e) {
	let { placement: t, targetNode: n, overlayNode: r, scrollNode: i, padding: a, shouldFlip: o, boundaryElement: s, offset: c, crossOffset: l, maxHeight: u, arrowSize: d = 0, arrowBoundaryOffset: f = 0, targetRect: p } = e, m = Al(), h = r instanceof HTMLElement ? Wl(r) : document.documentElement, g = h === document.documentElement, _ = window.getComputedStyle(h).position, v = !!_ && _ !== "static", y = g ? Hl(n, !1, p) : Ul(n, h, !1, p);
	if (!g) {
		let { marginTop: e, marginLeft: t } = window.getComputedStyle(n);
		y.top += parseInt(e, 10) || 0, y.left += parseInt(t, 10) || 0;
	}
	let b = Hl(r, !0), x = Pl(r);
	b.width += (x.left ?? 0) + (x.right ?? 0), b.height += (x.top ?? 0) + (x.bottom ?? 0);
	let S = Ml(i), C = jl(s, m), w = jl(h, m), T;
	if ((s.tagName === "BODY" || s.tagName === "HTML") && !g) {
		let e = Vl(h, !1);
		T = {
			top: -(e.top - C.top),
			left: -(e.left - C.left),
			width: 0,
			height: 0
		};
	} else T = (s.tagName === "BODY" || s.tagName === "HTML") && g ? {
		top: 0,
		left: 0,
		width: 0,
		height: 0
	} : Ul(s, h, !1);
	let E = z(s, h);
	return zl(t, y, b, S, x, a, o, C, w, T, c, l, v, u, d, f, E, m);
}
function Vl(e, t) {
	let { top: n, left: r, width: i, height: a } = e.getBoundingClientRect();
	return t && e instanceof e.ownerDocument.defaultView.HTMLElement && (i = e.offsetWidth, a = e.offsetHeight), {
		top: n,
		left: r,
		width: i,
		height: a
	};
}
function Hl(e, t, n) {
	let { top: r, left: i, width: a, height: o } = n || Vl(e, t), { scrollTop: s, scrollLeft: c, clientTop: l, clientLeft: u } = document.documentElement;
	return {
		top: r + s - l,
		left: i + c - u,
		width: a,
		height: o
	};
}
function Ul(e, t, n, r) {
	let i = window.getComputedStyle(e), a;
	if (i.position === "fixed") a = r || Vl(e, n);
	else {
		a = Hl(e, n, r);
		let i = Hl(t, n), o = window.getComputedStyle(t);
		i.top += (parseInt(o.borderTopWidth, 10) || 0) - t.scrollTop, i.left += (parseInt(o.borderLeftWidth, 10) || 0) - t.scrollLeft, a.top -= i.top, a.left -= i.left;
	}
	return a.top -= parseInt(i.marginTop, 10) || 0, a.left -= parseInt(i.marginLeft, 10) || 0, a;
}
function Wl(e) {
	let t = e.offsetParent;
	if (t && t === document.body && window.getComputedStyle(t).position === "static" && !Gl(t) && (t = document.documentElement), t == null) for (t = e.parentElement; t && !Gl(t);) t = t.parentElement;
	return t || document.documentElement;
}
function Gl(e) {
	let t = window.getComputedStyle(e);
	return t.transform !== "none" || /transform|perspective/.test(t.willChange) || t.filter !== "none" || t.contain === "paint" || "backdropFilter" in t && t.backdropFilter !== "none" || "WebkitBackdropFilter" in t && t.WebkitBackdropFilter !== "none";
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/useOverlayPosition.mjs
var Kl = typeof document < "u" ? window.visualViewport : null;
function ql(e) {
	let { direction: t } = Oi(), { arrowSize: n, targetRef: r, overlayRef: i, arrowRef: a, scrollRef: o = i, placement: s = "bottom", containerPadding: c = 12, shouldFlip: l = !0, boundaryElement: u = typeof document < "u" ? document.body : null, offset: d = 0, crossOffset: f = 0, shouldUpdatePosition: p = !0, isOpen: m = !0, onClose: h, maxHeight: g, arrowBoundaryOffset: _ = 0, getTargetRect: v } = e, [y, x] = (0, b.useState)(null), S = [
		p,
		s,
		i.current,
		r.current,
		a?.current,
		o.current,
		c,
		l,
		u,
		d,
		f,
		m,
		t,
		g,
		_,
		n
	], C = (0, b.useRef)(Kl?.scale);
	(0, b.useEffect)(() => {
		m && (C.current = Kl?.scale);
	}, [m]);
	let w = (0, b.useCallback)(() => {
		if (p === !1 || !m || !i.current || !r.current || !u || Kl?.scale !== C.current) return;
		let e = null;
		if (o.current && Nt(o.current)) {
			let t = jt()?.getBoundingClientRect(), n = o.current.getBoundingClientRect();
			e = {
				type: "top",
				offset: (t?.top ?? 0) - n.top
			}, e.offset > n.height / 2 && (e.type = "bottom", e.offset = (t?.bottom ?? 0) - n.bottom);
		}
		let h = i.current;
		!g && i.current && (h.style.top = "0px", h.style.bottom = "", h.style.maxHeight = (window.visualViewport?.height ?? window.innerHeight) + "px");
		let y = Bl({
			placement: Yl(s, t),
			overlayNode: i.current,
			targetNode: r.current,
			scrollNode: o.current || i.current,
			padding: c,
			shouldFlip: l,
			boundaryElement: u,
			offset: d,
			crossOffset: f,
			maxHeight: g,
			arrowSize: n ?? (a?.current ? Vl(a.current, !0).width : 0),
			arrowBoundaryOffset: _,
			targetRect: v?.(r.current)
		});
		if (!y.position) return;
		h.style.top = "", h.style.bottom = "", h.style.left = "", h.style.right = "", Object.keys(y.position).forEach((e) => h.style[e] = y.position[e] + "px"), h.style.maxHeight = y.maxHeight == null ? "" : y.maxHeight + "px";
		let b = jt();
		if (e && b && o.current) {
			let t = b.getBoundingClientRect(), n = o.current.getBoundingClientRect(), r = t[e.type] - n[e.type];
			o.current.scrollTop += r - e.offset;
		}
		x(y);
	}, S);
	H(w, S), Jl(w), jc({
		ref: i,
		onResize: w
	}), jc({
		ref: r,
		onResize: w
	});
	let T = (0, b.useRef)(!1);
	H(() => {
		let e, t = () => {
			T.current = !0, clearTimeout(e), e = setTimeout(() => {
				T.current = !1;
			}, 500), w();
		}, n = () => {
			T.current && t();
		};
		Kl?.addEventListener("resize", t), Kl?.addEventListener("scroll", n);
		let r = Dt(Mt(window), "scroll", n);
		return () => {
			Kl?.removeEventListener("resize", t), Kl?.removeEventListener("scroll", n), r();
		};
	}, [w]);
	let E = (0, b.useCallback)(() => {
		T.current || h?.();
	}, [h, T]);
	return Vs({
		triggerRef: r,
		isOpen: m,
		onClose: h && E
	}), {
		overlayProps: { style: {
			position: y ? "absolute" : "fixed",
			top: y ? void 0 : 0,
			left: y ? void 0 : 0,
			zIndex: 1e5,
			...y?.position,
			maxHeight: y?.maxHeight ?? "100vh"
		} },
		placement: y?.placement ?? null,
		triggerAnchorPoint: y?.triggerAnchorPoint ?? null,
		arrowProps: {
			"aria-hidden": "true",
			role: "presentation",
			style: {
				left: y?.arrowOffsetLeft,
				top: y?.arrowOffsetTop
			}
		},
		updatePosition: w
	};
}
function Jl(e) {
	H(() => (window.addEventListener("resize", e, !1), () => {
		window.removeEventListener("resize", e, !1);
	}), [e]);
}
function Yl(e, t) {
	return t === "rtl" ? e.replace("start", "right").replace("end", "left") : e.replace("start", "left").replace("end", "right");
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/usePopover.mjs
function Xl(e, t) {
	let { triggerRef: n, popoverRef: r, groupRef: i, isNonModal: a, isKeyboardDismissDisabled: o, shouldCloseOnInteractOutside: s, ...c } = e, l = c.trigger === "SubmenuTrigger", { overlayProps: u, underlayProps: d } = hl({
		isOpen: t.isOpen,
		onClose: t.close,
		shouldCloseOnBlur: !0,
		isDismissable: !a || l,
		isKeyboardDismissDisabled: o,
		shouldCloseOnInteractOutside: s
	}, i ?? r), { overlayProps: f, arrowProps: p, placement: m, triggerAnchorPoint: h } = ql({
		...c,
		targetRef: n,
		overlayRef: r,
		isOpen: t.isOpen,
		onClose: a && !l ? t.close : null,
		getTargetRect: c.getTargetRect ?? (t.point ? () => new DOMRect(t.point.x, t.point.y, 0, 0) : void 0)
	});
	yl({ isDisabled: a || !t.isOpen }), (0, b.useEffect)(() => {
		if (t.isOpen && r.current) return a ? Go(i?.current ?? r.current) : Wo([i?.current ?? r.current], { shouldUseInert: !0 });
	}, [
		a,
		t.isOpen,
		r,
		i
	]);
	let { focusWithinProps: g } = jo(e);
	return {
		popoverProps: U(u, f, g),
		arrowProps: p,
		underlayProps: d,
		placement: m,
		triggerAnchorPoint: h
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/radio/utils.mjs
var Zl = /* @__PURE__ */ new WeakMap();
//#endregion
//#region node_modules/react-aria/dist/private/radio/useRadio.mjs
function Ql(e, t, n) {
	let { value: r, children: i, "aria-label": a, "aria-labelledby": o, onPressStart: s, onPressEnd: c, onPressChange: l, onPress: u, onPressUp: d, onClick: f } = e, p = e.isDisabled || t.isDisabled, m = t.selectedValue === r, h = (e) => {
		e.stopPropagation(), t.setSelectedValue(r);
	}, { pressProps: g, isPressed: _ } = ua({
		onPressStart: s,
		onPressEnd: c,
		onPressChange: l,
		onPress: u,
		onPressUp: d,
		onClick: f,
		isDisabled: p
	}), { pressProps: v, isPressed: y } = ua({
		onPressStart: s,
		onPressEnd: c,
		onPressChange: l,
		onPressUp: d,
		onClick: f,
		isDisabled: p,
		onPress(e) {
			u?.(e), t.setSelectedValue(r), n.current?.focus();
		}
	}), { focusableProps: x } = Nr(U(e, { onFocus: () => t.setLastFocusedValue(r) }), n), S = U(g, x), C = Yi(e, { labelable: !0 }), w = -1;
	t.selectedValue == null ? (t.lastFocusedValue === r || t.lastFocusedValue == null) && (w = 0) : t.selectedValue === r && (w = 0), p && (w = void 0);
	let { name: T, form: E, descriptionId: D, errorMessageId: O, validationBehavior: k } = Zl.get(t);
	so(n, t.defaultSelectedValue, t.setSelectedValue), co({ validationBehavior: k }, t, n);
	let A = mo();
	return {
		labelProps: U(v, (0, b.useMemo)(() => ({
			onClick: (e) => e.preventDefault(),
			onMouseDown: (e) => e.preventDefault()
		}), [])),
		inputProps: U(C, {
			...S,
			type: "radio",
			name: T,
			form: E,
			tabIndex: w,
			disabled: p,
			required: t.isRequired && k === "native",
			checked: m,
			value: r,
			onChange: h,
			"aria-describedby": [
				e["aria-describedby"],
				A.id,
				t.isInvalid ? O : null,
				D
			].filter(Boolean).join(" ") || void 0
		}),
		descriptionProps: A,
		isDisabled: p,
		isSelected: m,
		isPressed: _ || y
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/radio/useRadioGroup.mjs
function $l(e, t) {
	let { name: n, form: r, isReadOnly: i, isRequired: a, isDisabled: o, orientation: s = "vertical", validationBehavior: c = "aria" } = e, { direction: l } = Oi(), { isInvalid: u, validationErrors: d, validationDetails: f } = t.displayValidation, { labelProps: p, fieldProps: m, descriptionProps: h, errorMessageProps: g } = Ao({
		...e,
		labelElementType: "span",
		isInvalid: t.isInvalid,
		errorMessage: e.errorMessage || d
	}), _ = Yi(e, { labelable: !0 }), { focusWithinProps: v } = jo({
		onBlurWithin(n) {
			e.onBlur?.(n), t.selectedValue || t.setLastFocusedValue(null);
		},
		onFocusWithin: e.onFocus,
		onFocusWithinChange: e.onFocusChange
	});
	function y(e, n) {
		let r = Wa(n.currentTarget, {
			from: B(n),
			accept: (e) => e instanceof St(e).HTMLInputElement && e.type === "radio"
		}), i;
		return e === "next" ? (i = r.nextNode(), i ||= (r.currentNode = n.currentTarget, r.firstChild())) : (i = r.previousNode(), i ||= (r.currentNode = n.currentTarget, r.lastChild())), i ? (i.focus(), t.setSelectedValue(i.value), !0) : !1;
	}
	let { keyboardProps: b } = Or({
		shortcuts: {
			ArrowRight: (e) => y(l === "rtl" && s !== "vertical" ? "prev" : "next", e),
			ArrowLeft: (e) => y(l === "rtl" && s !== "vertical" ? "next" : "prev", e),
			ArrowDown: (e) => y("next", e),
			ArrowUp: (e) => y("prev", e)
		},
		allowRepeats: !0
	}), x = sr(n);
	return Zl.set(t, {
		name: x,
		form: r,
		descriptionId: h.id,
		errorMessageId: g.id,
		validationBehavior: c
	}), {
		radioGroupProps: U(_, {
			role: "radiogroup",
			...b,
			"aria-invalid": t.isInvalid || void 0,
			"aria-errormessage": e["aria-errormessage"],
			"aria-readonly": i || void 0,
			"aria-required": a || void 0,
			"aria-disabled": o || void 0,
			"aria-orientation": s,
			...m,
			...v
		}),
		labelProps: p,
		descriptionProps: h,
		errorMessageProps: g,
		isInvalid: u,
		validationErrors: d,
		validationDetails: f
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/select/useSelect.mjs
var eu = /* @__PURE__ */ new WeakMap();
function tu(e, t, n) {
	let { keyboardDelegate: r, isDisabled: i, isRequired: a, name: o, form: s, validationBehavior: c = "aria" } = e, l = ic({
		usage: "search",
		sensitivity: "base"
	}), u = (0, b.useMemo)(() => r || new ts(t.collection, t.disabledKeys, n, l), [
		r,
		t.collection,
		t.disabledKeys,
		l,
		n
	]), { menuTriggerProps: d, menuProps: f } = Ws({
		isDisabled: i,
		type: "listbox"
	}, t, n), { keyboardProps: p } = Or({
		shortcuts: {
			ArrowLeft: () => {
				if (t.selectionManager.selectionMode === "multiple") return !1;
				let e = t.selectedKey == null ? u.getFirstKey?.() : u.getKeyAbove?.(t.selectedKey);
				e != null && t.setSelectedKey(e);
			},
			ArrowRight: () => {
				if (t.selectionManager.selectionMode === "multiple") return !1;
				let e = t.selectedKey == null ? u.getFirstKey?.() : u.getKeyBelow?.(t.selectedKey);
				e != null && t.setSelectedKey(e);
			}
		},
		allowRepeats: !0,
		onKeyDown: e.onKeyDown,
		onKeyUp: e.onKeyUp
	}), { typeSelectProps: m } = Ks({
		keyboardDelegate: u,
		selectionManager: t.selectionManager,
		onTypeSelect(e) {
			t.setSelectedKey(e);
		}
	}), { isInvalid: h, validationErrors: g, validationDetails: _ } = t.displayValidation, { labelProps: v, fieldProps: y, descriptionProps: x, errorMessageProps: S } = Ao({
		...e,
		labelElementType: "span",
		isInvalid: h,
		errorMessage: e.errorMessage || g
	});
	t.selectionManager.selectionMode === "multiple" && (m = {});
	let C = Yi(e, { labelable: !0 }), w = U(m, d, y), T = sr();
	return eu.set(t, {
		isDisabled: i,
		isRequired: a,
		name: o,
		form: s,
		validationBehavior: c
	}), {
		labelProps: {
			...v,
			onClick: () => {
				e.isDisabled || (n.current?.focus(), Gn("keyboard"));
			}
		},
		triggerProps: U(C, {
			...w,
			isDisabled: i,
			onKeyDown: tr(w.onKeyDown, p.onKeyDown),
			onKeyUp: p.onKeyUp,
			"aria-labelledby": [
				T,
				w["aria-labelledby"],
				w["aria-label"] && !w["aria-labelledby"] ? w.id : null
			].filter(Boolean).join(" "),
			onFocus(n) {
				t.isFocused || (e.onFocus && e.onFocus(n), e.onFocusChange && e.onFocusChange(!0), t.setFocused(!0));
			},
			onBlur(n) {
				t.isOpen || (e.onBlur && e.onBlur(n), e.onFocusChange && e.onFocusChange(!1), t.setFocused(!1));
			}
		}),
		valueProps: { id: T },
		menuProps: {
			...f,
			onAction: void 0,
			autoFocus: t.focusStrategy || !0,
			shouldSelectOnPressUp: !0,
			shouldFocusOnHover: !0,
			disallowEmptySelection: !0,
			linkBehavior: "selection",
			onBlur: (n) => {
				z(n.currentTarget, n.relatedTarget) || (e.onBlur && e.onBlur(n), e.onFocusChange && e.onFocusChange(!1), t.setFocused(!1));
			},
			"aria-labelledby": [y["aria-labelledby"], w["aria-label"] && !y["aria-labelledby"] ? w.id : null].filter(Boolean).join(" ")
		},
		descriptionProps: x,
		errorMessageProps: S,
		isInvalid: h,
		validationErrors: g,
		validationDetails: _,
		hiddenSelectProps: {
			isDisabled: i,
			name: o,
			label: e.label,
			state: t,
			triggerRef: n,
			form: s
		}
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/select/HiddenSelect.mjs
function nu(e, t, n) {
	let r = eu.get(t) || {}, { autoComplete: i, name: a = r.name, form: o = r.form, isDisabled: s = r.isDisabled } = e, { validationBehavior: c, isRequired: l } = r, { visuallyHiddenProps: u } = G({ style: {
		position: "fixed",
		top: 0,
		left: 0
	} });
	so(e.selectRef, t.defaultValue, t.setValue), co({
		validationBehavior: c,
		focus: () => n.current?.focus()
	}, t, e.selectRef);
	let d = t.setValue, f = (0, b.useCallback)((e) => {
		let t = B(e);
		t.multiple ? d(Array.from(t.selectedOptions, (e) => e.value)) : d(e.currentTarget.value);
	}, [d]);
	return {
		containerProps: {
			...u,
			"aria-hidden": !0,
			"data-react-aria-prevent-focus": !0,
			"data-a11y-ignore": "aria-hidden-focus"
		},
		inputProps: { style: { display: "none" } },
		selectProps: {
			tabIndex: -1,
			autoComplete: i,
			disabled: s,
			multiple: t.selectionManager.selectionMode === "multiple",
			required: c === "native" && l,
			name: a,
			form: o,
			value: t.value ?? "",
			onChange: f,
			onInput: f
		}
	};
}
function ru(e) {
	let { state: t, triggerRef: n, label: r, name: i, form: a, isDisabled: o } = e, s = (0, b.useRef)(null), c = (0, b.useRef)(null), { containerProps: l, selectProps: u } = nu({
		...e,
		selectRef: t.collection.size <= 300 ? s : c
	}, t, n), d = Array.isArray(t.value) ? t.value : [t.value];
	if (t.collection.size <= 300) return /*#__PURE__*/ b.createElement("div", {
		...l,
		"data-testid": "hidden-select-container"
	}, /*#__PURE__*/ b.createElement("label", null, r, /*#__PURE__*/ b.createElement("select", {
		...u,
		ref: s
	}, /*#__PURE__*/ b.createElement("option", {
		value: "",
		label: "\xA0"
	}, "\xA0"), [...t.collection.getKeys()].map((e) => {
		let n = t.collection.getItem(e);
		if (n && n.type === "item") return /*#__PURE__*/ b.createElement("option", {
			key: n.key,
			value: n.key
		}, n.textValue);
	}), t.collection.size === 0 && i && d.map((e, t) => /*#__PURE__*/ b.createElement("option", {
		key: t,
		value: e ?? ""
	})))));
	if (i) {
		let { validationBehavior: e } = eu.get(t) || {};
		d.length === 0 && (d = [null]);
		let n = d.map((t, n) => {
			let r = {
				type: "hidden",
				autoComplete: u.autoComplete,
				name: i,
				form: a,
				disabled: o,
				value: t ?? ""
			};
			return e === "native" ? /*#__PURE__*/ b.createElement("input", {
				key: n,
				...r,
				ref: n === 0 ? c : null,
				style: { display: "none" },
				type: "text",
				required: n === 0 && u.required,
				onChange: () => {}
			}) : /*#__PURE__*/ b.createElement("input", {
				key: n,
				...r,
				ref: n === 0 ? c : null
			});
		});
		return /*#__PURE__*/ b.createElement(b.Fragment, null, n);
	}
	return null;
}
//#endregion
//#region node_modules/react-aria/dist/private/switch/useSwitch.mjs
function iu(e, t, n) {
	let { labelProps: r, inputProps: i, isSelected: a, ...o } = Eo(e, t, n);
	return {
		labelProps: r,
		inputProps: {
			...i,
			role: "switch",
			checked: a
		},
		isSelected: a,
		...o
	};
}
//#endregion
//#region node_modules/scheduler/cjs/scheduler.production.js
var au = /* @__PURE__ */ p(((e) => {
	function t(e, t) {
		var n = e.length;
		e.push(t);
		a: for (; 0 < n;) {
			var r = n - 1 >>> 1, a = e[r];
			if (0 < i(a, t)) e[r] = t, e[n] = a, n = r;
			else break a;
		}
	}
	function n(e) {
		return e.length === 0 ? null : e[0];
	}
	function r(e) {
		if (e.length === 0) return null;
		var t = e[0], n = e.pop();
		if (n !== t) {
			e[0] = n;
			a: for (var r = 0, a = e.length, o = a >>> 1; r < o;) {
				var s = 2 * (r + 1) - 1, c = e[s], l = s + 1, u = e[l];
				if (0 > i(c, n)) l < a && 0 > i(u, c) ? (e[r] = u, e[l] = n, r = l) : (e[r] = c, e[s] = n, r = s);
				else if (l < a && 0 > i(u, n)) e[r] = u, e[l] = n, r = l;
				else break a;
			}
		}
		return t;
	}
	function i(e, t) {
		var n = e.sortIndex - t.sortIndex;
		return n === 0 ? e.id - t.id : n;
	}
	if (e.unstable_now = void 0, typeof performance == "object" && typeof performance.now == "function") {
		var a = performance;
		e.unstable_now = function() {
			return a.now();
		};
	} else {
		var o = Date, s = o.now();
		e.unstable_now = function() {
			return o.now() - s;
		};
	}
	var c = [], l = [], u = 1, d = null, f = 3, p = !1, m = !1, h = !1, g = !1, _ = typeof setTimeout == "function" ? setTimeout : null, v = typeof clearTimeout == "function" ? clearTimeout : null, y = typeof setImmediate < "u" ? setImmediate : null;
	function b(e) {
		for (var i = n(l); i !== null;) {
			if (i.callback === null) r(l);
			else if (i.startTime <= e) r(l), i.sortIndex = i.expirationTime, t(c, i);
			else break;
			i = n(l);
		}
	}
	function x(e) {
		if (h = !1, b(e), !m) {
			if (n(c) !== null) m = !0, S || (S = !0, O());
			else {
				var t = n(l);
				t !== null && j(x, t.startTime - e);
			}
		}
	}
	var S = !1, C = -1, w = 5, T = -1;
	function E() {
		return g ? !0 : !(e.unstable_now() - T < w);
	}
	function D() {
		if (g = !1, S) {
			var t = e.unstable_now();
			T = t;
			var i = !0;
			try {
				a: {
					m = !1, h && (h = !1, v(C), C = -1), p = !0;
					var a = f;
					try {
						b: {
							for (b(t), d = n(c); d !== null && !(d.expirationTime > t && E());) {
								var o = d.callback;
								if (typeof o == "function") {
									d.callback = null, f = d.priorityLevel;
									var s = o(d.expirationTime <= t);
									if (t = e.unstable_now(), typeof s == "function") {
										d.callback = s, b(t), i = !0;
										break b;
									}
									d === n(c) && r(c), b(t);
								} else r(c);
								d = n(c);
							}
							if (d !== null) i = !0;
							else {
								var u = n(l);
								u !== null && j(x, u.startTime - t), i = !1;
							}
						}
						break a;
					} finally {
						d = null, f = a, p = !1;
					}
					i = void 0;
				}
			} finally {
				i ? O() : S = !1;
			}
		}
	}
	var O;
	if (typeof y == "function") O = function() {
		y(D);
	};
	else if (typeof MessageChannel < "u") {
		var k = new MessageChannel(), A = k.port2;
		k.port1.onmessage = D, O = function() {
			A.postMessage(null);
		};
	} else O = function() {
		_(D, 0);
	};
	function j(t, n) {
		C = _(function() {
			t(e.unstable_now());
		}, n);
	}
	e.unstable_IdlePriority = 5, e.unstable_ImmediatePriority = 1, e.unstable_LowPriority = 4, e.unstable_NormalPriority = 3, e.unstable_Profiling = null, e.unstable_UserBlockingPriority = 2, e.unstable_cancelCallback = function(e) {
		e.callback = null;
	}, e.unstable_forceFrameRate = function(e) {
		0 > e || 125 < e ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : w = 0 < e ? Math.floor(1e3 / e) : 5;
	}, e.unstable_getCurrentPriorityLevel = function() {
		return f;
	}, e.unstable_next = function(e) {
		switch (f) {
			case 1:
			case 2:
			case 3:
				var t = 3;
				break;
			default: t = f;
		}
		var n = f;
		f = t;
		try {
			return e();
		} finally {
			f = n;
		}
	}, e.unstable_requestPaint = function() {
		g = !0;
	}, e.unstable_runWithPriority = function(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 3:
			case 4:
			case 5: break;
			default: e = 3;
		}
		var n = f;
		f = e;
		try {
			return t();
		} finally {
			f = n;
		}
	}, e.unstable_scheduleCallback = function(r, i, a) {
		var o = e.unstable_now();
		switch (typeof a == "object" && a ? (a = a.delay, a = typeof a == "number" && 0 < a ? o + a : o) : a = o, r) {
			case 1:
				var s = -1;
				break;
			case 2:
				s = 250;
				break;
			case 5:
				s = 1073741823;
				break;
			case 4:
				s = 1e4;
				break;
			default: s = 5e3;
		}
		return s = a + s, r = {
			id: u++,
			callback: i,
			priorityLevel: r,
			startTime: a,
			expirationTime: s,
			sortIndex: -1
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (v(C), C = -1) : h = !0, j(x, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, S || (S = !0, O()))), r;
	}, e.unstable_shouldYield = E, e.unstable_wrapCallback = function(e) {
		var t = f;
		return function() {
			var n = f;
			f = t;
			try {
				return e.apply(this, arguments);
			} finally {
				f = n;
			}
		};
	};
})), ou = /* @__PURE__ */ p(((e, t) => {
	t.exports = au();
})), su = /* @__PURE__ */ p(((e) => {
	var t = ou(), n = _(), r = zr();
	function i(e) {
		var t = "https://react.dev/errors/" + e;
		if (1 < arguments.length) {
			t += "?args[]=" + encodeURIComponent(arguments[1]);
			for (var n = 2; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
		}
		return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
	}
	function a(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
	}
	function o(e) {
		for (var t = e, n = t; n && !n.alternate;) t = n, t.flags & 4098 && (e = t.return), n = t.return;
		for (; t.return;) t = t.return;
		return t.tag === 3 ? e : null;
	}
	function s(e) {
		if (e.tag === 13) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function c(e) {
		if (e.tag === 31) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function l(e) {
		if (o(e) !== e) throw Error(i(188));
	}
	function u(e) {
		var t = e.alternate;
		if (!t) {
			if (t = o(e), t === null) throw Error(i(188));
			return t === e ? e : null;
		}
		for (var n = e, r = t;;) {
			var a = n.return;
			if (a === null) break;
			var s = a.alternate;
			if (s === null) {
				if (r = a.return, r !== null) {
					n = r;
					continue;
				}
				break;
			}
			if (a.child === s.child) {
				for (s = a.child; s;) {
					if (s === n) return l(a), e;
					if (s === r) return l(a), t;
					s = s.sibling;
				}
				throw Error(i(188));
			}
			if (n.return !== r.return) n = a, r = s;
			else {
				for (var c = !1, u = a.child; u;) {
					if (u === n) {
						c = !0, n = a, r = s;
						break;
					}
					if (u === r) {
						c = !0, r = a, n = s;
						break;
					}
					u = u.sibling;
				}
				if (!c) {
					for (u = s.child; u;) {
						if (u === n) {
							c = !0, n = s, r = a;
							break;
						}
						if (u === r) {
							c = !0, r = s, n = a;
							break;
						}
						u = u.sibling;
					}
					if (!c) throw Error(i(189));
				}
			}
			if (n.alternate !== r) throw Error(i(190));
		}
		if (n.tag !== 3) throw Error(i(188));
		return n.stateNode.current === n ? e : t;
	}
	function d(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e;
		for (e = e.child; e !== null;) {
			if (t = d(e), t !== null) return t;
			e = e.sibling;
		}
		return null;
	}
	function f(e, t, n, r, i, a) {
		for (; e !== null;) {
			if ((e.tag === 5 || e.tag === 27 || e.tag === 6) && n(e, r, i, a) || (e.tag !== 22 || e.memoizedState === null) && (t || e.tag !== 5 && e.tag !== 27) && f(e.child, t, n, r, i, a)) return !0;
			e = e.sibling;
		}
		return !1;
	}
	function p(e) {
		for (e = e.return; e !== null;) {
			if (e.tag === 3 || e.tag === 5 || e.tag === 27) return e;
			e = e.return;
		}
		return null;
	}
	function m(e) {
		var t = !1;
		for (e = e.return; e !== null && (e.tag === 4 && (t = !0), e.tag !== 3 && e.tag !== 5 && e.tag !== 27);) e = e.return;
		return t;
	}
	function h(e) {
		var t = [null, null], n = p(e);
		return n === null || g(t, e, n.child, { foundSelf: !1 }), t;
	}
	function g(e, t, n, r) {
		for (; n !== null;) {
			if (n === t) r.foundSelf = !0;
			else if (n.tag === 5 || n.tag === 27 || n.tag === 6) {
				if (r.foundSelf) return e[1] = n, !0;
				e[0] = n;
			} else if ((n.tag !== 22 || n.memoizedState === null) && g(e, t, n.child, r)) return !0;
			n = n.sibling;
		}
		return !1;
	}
	function v(e) {
		switch (e.tag) {
			case 5:
			case 27:
			case 6: return e.stateNode;
			case 3: return e.stateNode.containerInfo;
			default: throw Error(i(559));
		}
	}
	var y = null, b = null;
	function x(e, t, n) {
		return e === n || e === t && (y = e, !0);
	}
	function S(e, t, n) {
		return e === n ? (b = e, !1) : e === t && (b !== null && (y = e), !0);
	}
	function C(e) {
		if (e === null) return null;
		do
			e = e === null ? null : e.return;
		while (e && e.tag !== 5 && e.tag !== 27 && e.tag !== 3);
		return e || null;
	}
	function w(e, t, n) {
		for (var r = 0, i = e; i; i = n(i)) r++;
		i = 0;
		for (var a = t; a; a = n(a)) i++;
		for (; 0 < r - i;) e = n(e), r--;
		for (; 0 < i - r;) t = n(t), i--;
		for (; r--;) {
			if (e === t || t !== null && e === t.alternate) return e;
			e = n(e), t = n(t);
		}
		return null;
	}
	var T = Object.assign, E = Symbol.for("react.element"), D = Symbol.for("react.transitional.element"), O = Symbol.for("react.portal"), k = Symbol.for("react.fragment"), A = Symbol.for("react.strict_mode"), j = Symbol.for("react.profiler"), M = Symbol.for("react.consumer"), N = Symbol.for("react.context"), ee = Symbol.for("react.forward_ref"), te = Symbol.for("react.suspense"), P = Symbol.for("react.suspense_list"), ne = Symbol.for("react.memo"), F = Symbol.for("react.lazy"), re = Symbol.for("react.activity"), ie = Symbol.for("react.legacy_hidden"), ae = Symbol.for("react.memo_cache_sentinel"), oe = Symbol.for("react.view_transition"), se = Symbol.for("react.recoverable"), ce = Symbol.iterator;
	function le(e) {
		return typeof e != "object" || !e ? null : (e = ce && e[ce] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var ue = Symbol.for("react.client.reference");
	function de(e) {
		if (e == null) return null;
		if (typeof e == "function") return e.$$typeof === ue ? null : e.displayName || e.name || null;
		if (typeof e == "string") return e;
		switch (e) {
			case k: return "Fragment";
			case j: return "Profiler";
			case A: return "StrictMode";
			case te: return "Suspense";
			case P: return "SuspenseList";
			case re: return "Activity";
			case oe: return "ViewTransition";
		}
		if (typeof e == "object") switch (e.$$typeof) {
			case O: return "Portal";
			case N: return e.displayName || "Context";
			case M: return (e._context.displayName || "Context") + ".Consumer";
			case ee:
				var t = e.render;
				return e = e.displayName, e ||= (e = t.displayName || t.name || "", e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
			case ne: return t = e.displayName || null, t === null ? de(e.type) || "Memo" : t;
			case F:
				t = e._payload, e = e._init;
				try {
					return de(e(t));
				} catch {}
		}
		return null;
	}
	var fe = Array.isArray, I = n.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, L = r.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, pe = {
		pending: !1,
		data: null,
		method: null,
		action: null
	}, me = [], he = -1;
	function ge(e) {
		return { current: e };
	}
	function _e(e) {
		0 > he || (e.current = me[he], me[he] = null, he--);
	}
	function ve(e, t) {
		he++, me[he] = e.current, e.current = t;
	}
	var ye = ge(null), be = ge(null), xe = ge(null), Se = ge(null);
	function Ce(e, t) {
		switch (ve(xe, t), ve(be, e), ve(ye, null), t.nodeType) {
			case 9:
			case 11:
				e = (e = t.documentElement) && (e = e.namespaceURI) ? up(e) : 0;
				break;
			default: if (e = t.tagName, t = t.namespaceURI) t = up(t), e = dp(t, e);
			else switch (e) {
				case "svg":
					e = 1;
					break;
				case "math":
					e = 2;
					break;
				default: e = 0;
			}
		}
		_e(ye), ve(ye, e);
	}
	function we() {
		_e(ye), _e(be), _e(xe);
	}
	function Te(e) {
		var t = e.memoizedState;
		t !== null && (sh._currentValue = t.memoizedState, ve(Se, e)), t = ye.current;
		var n = dp(t, e.type);
		t !== n && (ve(be, e), ve(ye, n));
	}
	function Ee(e) {
		be.current === e && (_e(ye), _e(be)), Se.current === e && (_e(Se), sh._currentValue = pe);
	}
	var De, Oe;
	function ke(e) {
		if (De === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			De = t && t[1] || "", Oe = -1 < e.stack.indexOf("\n    at") ? " (<anonymous>)" : -1 < e.stack.indexOf("@") ? "@unknown:0:0" : "";
		}
		return "\n" + De + e + Oe;
	}
	var Ae = !1;
	function je(e, t) {
		if (!e || Ae) return "";
		Ae = !0;
		var n = Error.prepareStackTrace;
		Error.prepareStackTrace = void 0;
		try {
			var r = { DetermineComponentFrameRoot: function() {
				try {
					if (t) {
						var n = function() {
							throw Error();
						};
						if (Object.defineProperty(n.prototype, "props", { set: function() {
							throw Error();
						} }), typeof Reflect == "object" && Reflect.construct) {
							try {
								Reflect.construct(n, []);
							} catch (e) {
								var r = e;
							}
							Reflect.construct(e, [], n);
						} else {
							try {
								n.call();
							} catch (e) {
								r = e;
							}
							n = !1;
							try {
								var i = Object.getOwnPropertyDescriptor(e.prototype, "props");
								Object.defineProperty(e.prototype, "props", {
									configurable: !0,
									set: function() {
										throw Error();
									}
								}), n = !0, new e();
							} finally {
								n && (i === void 0 ? delete e.prototype.props : Object.defineProperty(e.prototype, "props", i));
							}
						}
					} else {
						try {
							throw Error();
						} catch (e) {
							r = e;
						}
						(n = e()) && typeof n.catch == "function" && n.catch(function() {});
					}
				} catch (e) {
					if (e && r && typeof e.stack == "string") return [e.stack, r.stack];
				}
				return [null, null];
			} };
			r.DetermineComponentFrameRoot.displayName = "DetermineComponentFrameRoot";
			var i = Object.getOwnPropertyDescriptor(r.DetermineComponentFrameRoot, "name");
			i && i.configurable && Object.defineProperty(r.DetermineComponentFrameRoot, "name", { value: "DetermineComponentFrameRoot" });
			var a = r.DetermineComponentFrameRoot(), o = a[0], s = a[1];
			if (o && s) {
				var c = o.split("\n"), l = s.split("\n");
				for (i = r = 0; r < c.length && !c[r].includes("DetermineComponentFrameRoot");) r++;
				for (; i < l.length && !l[i].includes("DetermineComponentFrameRoot");) i++;
				if (r === c.length || i === l.length) for (r = c.length - 1, i = l.length - 1; 1 <= r && 0 <= i && c[r] !== l[i];) i--;
				for (; 1 <= r && 0 <= i; r--, i--) if (c[r] !== l[i]) {
					if (r !== 1 || i !== 1) do
						if (r--, i--, 0 > i || c[r] !== l[i]) {
							var u = "\n" + c[r].replace(" at new ", " at ");
							return e.displayName && u.includes("<anonymous>") && (u = u.replace("<anonymous>", e.displayName)), u;
						}
					while (1 <= r && 0 <= i);
					break;
				}
			}
		} finally {
			Ae = !1, Error.prepareStackTrace = n;
		}
		return (n = e ? e.displayName || e.name : "") ? ke(n) : "";
	}
	function Me(e, t) {
		switch (e.tag) {
			case 26:
			case 27:
			case 5: return ke(e.type);
			case 16: return ke("Lazy");
			case 13: return e.child !== t && t !== null ? ke("Suspense Fallback") : ke("Suspense");
			case 19: return ke("SuspenseList");
			case 0:
			case 15: return je(e.type, !1);
			case 11: return je(e.type.render, !1);
			case 1: return je(e.type, !0);
			case 31: return ke("Activity");
			case 30: return ke("ViewTransition");
			default: return "";
		}
	}
	function Ne(e) {
		try {
			var t = "", n = null;
			do
				t += Me(e, n), n = e, e = e.return;
			while (e);
			return t;
		} catch (e) {
			return "\nError generating stack: " + e.message + "\n" + e.stack;
		}
	}
	var Pe = Object.prototype.hasOwnProperty, Fe = t.unstable_scheduleCallback, Ie = t.unstable_cancelCallback, Le = t.unstable_shouldYield, Re = t.unstable_requestPaint, ze = t.unstable_now, Be = t.unstable_getCurrentPriorityLevel, Ve = t.unstable_ImmediatePriority, He = t.unstable_UserBlockingPriority, Ue = t.unstable_NormalPriority, We = t.unstable_LowPriority, Ge = t.unstable_IdlePriority, Ke = t.log, qe = t.unstable_setDisableYieldValue, Je = null, Ye = null;
	function Xe(e) {
		if (typeof Ke == "function" && qe(e), Ye && typeof Ye.setStrictMode == "function") try {
			Ye.setStrictMode(Je, e);
		} catch {}
	}
	var Ze = Math.clz32 ? Math.clz32 : et, Qe = Math.log, $e = Math.LN2;
	function et(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (Qe(e) / $e | 0) | 0;
	}
	var tt = 256, nt = 262144, rt = 4194304;
	function it(e) {
		var t = e & 42;
		if (t !== 0) return t;
		switch (e & -e) {
			case 1: return 1;
			case 2: return 2;
			case 4: return 4;
			case 8: return 8;
			case 16: return 16;
			case 32: return 32;
			case 64: return 64;
			case 128: return 128;
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072: return e & -e;
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return e & 3932160;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432: return e & 62914560;
			case 67108864: return 67108864;
			case 134217728: return 134217728;
			case 268435456: return 268435456;
			case 536870912: return 536870912;
			case 1073741824: return 0;
			default: return e;
		}
	}
	function at(e, t, n) {
		var r = e.pendingLanes;
		if (r === 0) return 0;
		var i = 0, a = e.suspendedLanes, o = e.pingedLanes;
		e = e.warmLanes;
		var s = r & 134217727;
		return s === 0 ? (s = r & ~a, s === 0 ? o === 0 ? n || (n = r & ~e, n !== 0 && (i = it(n))) : i = it(o) : i = it(s)) : (r = s & ~a, r === 0 ? (o &= s, o === 0 ? n || (n = s & ~e, n !== 0 && (i = it(n))) : i = it(o)) : i = it(r)), i === 0 ? 0 : t !== 0 && t !== i && (t & a) === 0 && (a = i & -i, n = t & -t, a >= n || a === 32 && n & 4194048) ? t : i;
	}
	function ot(e, t) {
		return (e.pendingLanes & ~(e.suspendedLanes & ~e.pingedLanes) & t) === 0;
	}
	function st(e, t) {
		t & 8 && (t |= t & 32);
		var n = e.entangledLanes;
		if (n !== 0) for (e = e.entanglements, n &= t; 0 < n;) {
			var r = 31 - Ze(n), i = 1 << r;
			t |= e[r], n &= ~i;
		}
		return t;
	}
	function ct(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 4:
			case 8:
			case 64: return t + 250;
			case 16:
			case 32:
			case 128:
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return t + 5e3;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432: return -1;
			case 67108864:
			case 134217728:
			case 268435456:
			case 536870912:
			case 1073741824: return -1;
			default: return -1;
		}
	}
	function lt() {
		var e = rt;
		return rt <<= 1, !(rt & 62914560) && (rt = 4194304), e;
	}
	function ut(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function dt(e, t) {
		e.pendingLanes |= t, t !== 268435456 && (e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0);
	}
	function ft(e, t, n, r, i, a) {
		var o = e.pendingLanes;
		e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0, e.expiredLanes &= n, e.entangledLanes &= n, e.errorRecoveryDisabledLanes &= n, e.shellSuspendCounter = 0;
		var s = e.entanglements, c = e.expirationTimes, l = e.hiddenUpdates;
		for (n = o & ~n; 0 < n;) {
			var u = 31 - Ze(n), d = 1 << u;
			s[u] = 0, c[u] = -1;
			var f = l[u];
			if (f !== null) for (l[u] = null, u = 0; u < f.length; u++) {
				var p = f[u];
				p !== null && (p.lane &= -536870913);
			}
			n &= ~d;
		}
		r !== 0 && pt(e, r, 0), a !== 0 && i === 0 && e.tag !== 0 && (e.suspendedLanes |= a & ~(o & ~t));
	}
	function pt(e, t, n) {
		e.pendingLanes |= t, e.suspendedLanes &= ~t;
		var r = 31 - Ze(t);
		e.entangledLanes |= t, e.entanglements[r] = e.entanglements[r] | 1073741824 | n & 261930;
	}
	function mt(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - Ze(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	function ht(e, t) {
		var n = t & -t;
		return n = n & 42 ? 1 : gt(n), (n & (e.suspendedLanes | t)) === 0 ? n : 0;
	}
	function gt(e) {
		switch (e) {
			case 2:
				e = 1;
				break;
			case 8:
				e = 4;
				break;
			case 32:
				e = 16;
				break;
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152:
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432:
				e = 128;
				break;
			case 268435456:
				e = 134217728;
				break;
			default: e = 0;
		}
		return e;
	}
	function _t(e) {
		return e &= -e, 2 < e ? 8 < e ? e & 134217727 ? 32 : 268435456 : 8 : 2;
	}
	function vt() {
		var e = L.p;
		return e === 0 ? (e = window.event, e === void 0 ? 32 : Ch(e.type)) : e;
	}
	function yt(e, t) {
		var n = L.p;
		try {
			return L.p = e, t();
		} finally {
			L.p = n;
		}
	}
	var bt = Math.random().toString(36).slice(2), xt = "__reactFiber$" + bt, R = "__reactProps$" + bt, St = "__reactContainer$" + bt, Ct = "__reactEvents$" + bt, wt = "__reactListeners$" + bt, Tt = "__reactHandles$" + bt, Et = "__reactResources$" + bt, Dt = "__reactMarker$" + bt, Ot = "__reactLoad$" + bt;
	function kt(e) {
		delete e[xt], delete e[R], delete e[wt], delete e[Tt];
	}
	function At(e) {
		var t;
		if (t = e[xt]) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[St] || n[xt]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = fm(e); e !== null;) {
					if (n = e[xt]) return n;
					e = fm(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function z(e) {
		if (e = e[xt] || e[St]) {
			var t = e.tag;
			if (t === 5 || t === 6 || t === 13 || t === 31 || t === 26 || t === 27 || t === 3) return e;
		}
		return null;
	}
	function jt(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e.stateNode;
		throw Error(i(33));
	}
	function B(e) {
		var t = e[Et];
		return t ||= e[Et] = {
			hoistableStyles: /* @__PURE__ */ new Map(),
			hoistableScripts: /* @__PURE__ */ new Map()
		}, t;
	}
	function Mt(e) {
		e[Dt] = !0;
	}
	function Nt(e) {
		e[Ot] = void 0;
	}
	var Pt = /* @__PURE__ */ new Set(), Ft = {};
	function It(e, t) {
		Lt(e, t), Lt(e + "Capture", t);
	}
	function Lt(e, t) {
		for (Ft[e] = t, e = 0; e < t.length; e++) Pt.add(t[e]);
	}
	var Rt = RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"), zt = {}, Bt = {};
	function Vt(e) {
		return Pe.call(Bt, e) ? !0 : Pe.call(zt, e) ? !1 : Rt.test(e) ? Bt[e] = !0 : (zt[e] = !0, !1);
	}
	var V = !1;
	function Ht() {
		var e = V;
		return V = !1, e;
	}
	function H(e, t, n) {
		if (Vt(t)) {
			if (n === null) e.removeAttribute(t);
			else {
				switch (typeof n) {
					case "undefined":
					case "function":
					case "symbol":
						e.removeAttribute(t);
						return;
					case "boolean":
						var r = t.toLowerCase().slice(0, 5);
						if (r !== "data-" && r !== "aria-") {
							e.removeAttribute(t);
							return;
						}
				}
				e.setAttribute(t, n);
			}
		}
	}
	function Ut(e, t, n) {
		if (n === null) e.removeAttribute(t);
		else {
			switch (typeof n) {
				case "undefined":
				case "function":
				case "symbol":
				case "boolean":
					e.removeAttribute(t);
					return;
			}
			e.setAttribute(t, n);
		}
	}
	function Wt(e, t, n, r) {
		if (r === null) e.removeAttribute(n);
		else {
			switch (typeof r) {
				case "undefined":
				case "function":
				case "symbol":
				case "boolean":
					e.removeAttribute(n);
					return;
			}
			e.setAttributeNS(t, n, r);
		}
	}
	function Gt(e) {
		switch (typeof e) {
			case "bigint":
			case "boolean":
			case "number":
			case "string":
			case "undefined": return e;
			case "object": return e;
			default: return "";
		}
	}
	function Kt(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function qt(e, t, n) {
		var r = Object.getOwnPropertyDescriptor(e.constructor.prototype, t);
		if (!e.hasOwnProperty(t) && r !== void 0 && typeof r.get == "function" && typeof r.set == "function") {
			var i = r.get, a = r.set;
			return Object.defineProperty(e, t, {
				configurable: !0,
				get: function() {
					return i.call(this);
				},
				set: function(e) {
					n = "" + e, a.call(this, e);
				}
			}), Object.defineProperty(e, t, { enumerable: r.enumerable }), {
				getValue: function() {
					return n;
				},
				setValue: function(e) {
					n = "" + e;
				},
				stopTracking: function() {
					e._valueTracker = null, delete e[t];
				}
			};
		}
	}
	function Jt(e) {
		if (!e._valueTracker) {
			var t = Kt(e) ? "checked" : "value";
			e._valueTracker = qt(e, t, "" + e[t]);
		}
	}
	function Yt(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = Kt(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== n && (t.setValue(e), !0);
	}
	var Xt = /[\n"\\]/g;
	function Zt(e) {
		return e.replace(Xt, function(e) {
			return "\\" + e.charCodeAt(0).toString(16) + " ";
		});
	}
	function Qt(e, t, n, r, i, a, o, s) {
		e.name = "", o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" ? e.type = o : e.removeAttribute("type"), t == null ? o !== "submit" && o !== "reset" || e.removeAttribute("value") : o === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + Gt(t)) : e.value !== "" + Gt(t) && (e.value = "" + Gt(t)), t == null ? n == null ? r != null && e.removeAttribute("value") : en(e, Gt(n)) : o === "number" && e.value == t ? en(e, Gt(e.value)) : en(e, Gt(t)), i == null && a != null && (e.defaultChecked = !!a), i != null && (e.checked = i && typeof i != "function" && typeof i != "symbol"), s != null && typeof s != "function" && typeof s != "symbol" && typeof s != "boolean" ? e.name = "" + Gt(s) : e.removeAttribute("name");
	}
	function $t(e, t, n, r, i, a, o, s) {
		if (a != null && typeof a != "function" && typeof a != "symbol" && typeof a != "boolean" && (e.type = a), t != null || n != null) {
			if (!(a !== "submit" && a !== "reset" || t != null)) {
				Jt(e);
				return;
			}
			n = n == null ? "" : "" + Gt(n), t = t == null ? n : "" + Gt(t), s || t === e.value || (e.value = t), e.defaultValue = t;
		}
		r ??= i, r = typeof r != "function" && typeof r != "symbol" && !!r, e.checked = s ? e.checked : !!r, e.defaultChecked = !!r, o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" && (e.name = o), Jt(e);
	}
	function en(e, t) {
		e.defaultValue !== "" + t && (e.defaultValue = "" + t);
	}
	function tn(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + Gt(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function nn(e, t, n) {
		if (t != null && (t = "" + Gt(t), t !== e.value && (e.value = t), n == null)) {
			e.defaultValue !== t && (e.defaultValue = t);
			return;
		}
		e.defaultValue = n == null ? "" : "" + Gt(n);
	}
	function rn(e, t, n, r) {
		if (t == null) {
			if (r != null) {
				if (n != null) throw Error(i(92));
				if (fe(r)) {
					if (1 < r.length) throw Error(i(93));
					r = r[0];
				}
				n = r;
			}
			n ??= "", t = n;
		}
		n = Gt(t), e.defaultValue = n, r = e.textContent, r === n && r !== "" && r !== null && (e.value = r), Jt(e);
	}
	function an(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var on = new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));
	function sn(e, t, n) {
		var r = t.indexOf("--") === 0;
		n == null || typeof n == "boolean" || n === "" ? r ? e.setProperty(t, "") : t === "float" ? e.cssFloat = "" : e[t] = "" : r ? e.setProperty(t, n) : typeof n != "number" || n === 0 || on.has(t) ? t === "float" ? e.cssFloat = n : e[t] = ("" + n).trim() : e[t] = n + "px";
	}
	function cn(e, t, n) {
		if (t != null && typeof t != "object") throw Error(i(62));
		if (e = e.style, n != null) {
			for (var r in n) !n.hasOwnProperty(r) || t != null && t.hasOwnProperty(r) || (r.indexOf("--") === 0 ? e.setProperty(r, "") : r === "float" ? e.cssFloat = "" : e[r] = "", V = !0);
			for (var a in t) r = t[a], t.hasOwnProperty(a) && n[a] !== r && (sn(e, a, r), V = !0);
		} else for (var o in t) t.hasOwnProperty(o) && sn(e, o, t[o]);
	}
	function ln(e) {
		if (e.indexOf("-") === -1) return !1;
		switch (e) {
			case "annotation-xml":
			case "color-profile":
			case "font-face":
			case "font-face-src":
			case "font-face-uri":
			case "font-face-format":
			case "font-face-name":
			case "missing-glyph": return !1;
			default: return !0;
		}
	}
	var un = /* @__PURE__ */ new Map([
		["acceptCharset", "accept-charset"],
		["htmlFor", "for"],
		["httpEquiv", "http-equiv"],
		["crossOrigin", "crossorigin"],
		["accentHeight", "accent-height"],
		["alignmentBaseline", "alignment-baseline"],
		["arabicForm", "arabic-form"],
		["baselineShift", "baseline-shift"],
		["capHeight", "cap-height"],
		["clipPath", "clip-path"],
		["clipRule", "clip-rule"],
		["colorInterpolation", "color-interpolation"],
		["colorInterpolationFilters", "color-interpolation-filters"],
		["colorProfile", "color-profile"],
		["colorRendering", "color-rendering"],
		["dominantBaseline", "dominant-baseline"],
		["enableBackground", "enable-background"],
		["fillOpacity", "fill-opacity"],
		["fillRule", "fill-rule"],
		["floodColor", "flood-color"],
		["floodOpacity", "flood-opacity"],
		["fontFamily", "font-family"],
		["fontSize", "font-size"],
		["fontSizeAdjust", "font-size-adjust"],
		["fontStretch", "font-stretch"],
		["fontStyle", "font-style"],
		["fontVariant", "font-variant"],
		["fontWeight", "font-weight"],
		["glyphName", "glyph-name"],
		["glyphOrientationHorizontal", "glyph-orientation-horizontal"],
		["glyphOrientationVertical", "glyph-orientation-vertical"],
		["horizAdvX", "horiz-adv-x"],
		["horizOriginX", "horiz-origin-x"],
		["imageRendering", "image-rendering"],
		["letterSpacing", "letter-spacing"],
		["lightingColor", "lighting-color"],
		["markerEnd", "marker-end"],
		["markerMid", "marker-mid"],
		["markerStart", "marker-start"],
		["maskType", "mask-type"],
		["overlinePosition", "overline-position"],
		["overlineThickness", "overline-thickness"],
		["paintOrder", "paint-order"],
		["panose-1", "panose-1"],
		["pointerEvents", "pointer-events"],
		["renderingIntent", "rendering-intent"],
		["shapeRendering", "shape-rendering"],
		["stopColor", "stop-color"],
		["stopOpacity", "stop-opacity"],
		["strikethroughPosition", "strikethrough-position"],
		["strikethroughThickness", "strikethrough-thickness"],
		["strokeDasharray", "stroke-dasharray"],
		["strokeDashoffset", "stroke-dashoffset"],
		["strokeLinecap", "stroke-linecap"],
		["strokeLinejoin", "stroke-linejoin"],
		["strokeMiterlimit", "stroke-miterlimit"],
		["strokeOpacity", "stroke-opacity"],
		["strokeWidth", "stroke-width"],
		["textAnchor", "text-anchor"],
		["textDecoration", "text-decoration"],
		["textRendering", "text-rendering"],
		["transformOrigin", "transform-origin"],
		["underlinePosition", "underline-position"],
		["underlineThickness", "underline-thickness"],
		["unicodeBidi", "unicode-bidi"],
		["unicodeRange", "unicode-range"],
		["unitsPerEm", "units-per-em"],
		["vAlphabetic", "v-alphabetic"],
		["vHanging", "v-hanging"],
		["vIdeographic", "v-ideographic"],
		["vMathematical", "v-mathematical"],
		["vectorEffect", "vector-effect"],
		["vertAdvY", "vert-adv-y"],
		["vertOriginX", "vert-origin-x"],
		["vertOriginY", "vert-origin-y"],
		["wordSpacing", "word-spacing"],
		["writingMode", "writing-mode"],
		["xmlnsXlink", "xmlns:xlink"],
		["xHeight", "x-height"]
	]), dn = /^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;
	function fn(e) {
		return dn.test("" + e) ? "javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')" : e;
	}
	function pn() {}
	var mn = null;
	function hn(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var gn = null, _n = null;
	function vn(e) {
		var t = z(e);
		if (t && (e = t.stateNode)) {
			var n = e[R] || null;
			a: switch (e = t.stateNode, t.type) {
				case "input":
					if (Qt(e, n.value, n.defaultValue, n.defaultValue, n.checked, n.defaultChecked, n.type, n.name), t = n.name, n.type === "radio" && t != null) {
						for (n = e; n.parentNode;) n = n.parentNode;
						for (n = n.querySelectorAll("input[name=\"" + Zt("" + t) + "\"][type=\"radio\"]"), t = 0; t < n.length; t++) {
							var r = n[t];
							if (r !== e && r.form === e.form) {
								var a = r[R] || null;
								if (!a) throw Error(i(90));
								Qt(r, a.value, a.defaultValue, a.defaultValue, a.checked, a.defaultChecked, a.type, a.name);
							}
						}
						for (t = 0; t < n.length; t++) r = n[t], r.form === e.form && Yt(r);
					}
					break a;
				case "textarea":
					nn(e, n.value, n.defaultValue);
					break a;
				case "select": t = n.value, t != null && tn(e, !!n.multiple, t, !1);
			}
		}
	}
	var yn = !1;
	function bn(e, t, n) {
		if (yn) return e(t, n);
		yn = !0;
		try {
			return e(t);
		} finally {
			if (yn = !1, (gn !== null || _n !== null) && (Ld(), gn && (t = gn, e = _n, _n = gn = null, vn(t), e))) for (t = 0; t < e.length; t++) vn(e[t]);
		}
	}
	function xn(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var r = n[R] || null;
		if (r === null) return null;
		n = r[t];
		a: switch (t) {
			case "onClick":
			case "onClickCapture":
			case "onDoubleClick":
			case "onDoubleClickCapture":
			case "onMouseDown":
			case "onMouseDownCapture":
			case "onMouseMove":
			case "onMouseMoveCapture":
			case "onMouseUp":
			case "onMouseUpCapture":
			case "onMouseEnter":
				(r = !r.disabled) || (e = e.type, r = e !== "button" && e !== "input" && e !== "select" && e !== "textarea"), e = !r;
				break a;
			default: e = !1;
		}
		if (e) return null;
		if (n && typeof n != "function") throw Error(i(231, t, typeof n));
		return n;
	}
	var Sn = !(typeof window > "u" || window.document === void 0 || window.document.createElement === void 0), Cn = !1;
	if (Sn) try {
		var wn = {};
		Object.defineProperty(wn, "passive", { get: function() {
			Cn = !0;
		} }), window.addEventListener("test", wn, wn), window.removeEventListener("test", wn, wn);
	} catch {
		Cn = !1;
	}
	var Tn = null, En = null, Dn = null;
	function On() {
		if (Dn) return Dn;
		var e, t = En, n = t.length, r, i = "value" in Tn ? Tn.value : Tn.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return Dn = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function kn(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function An() {
		return !0;
	}
	function jn() {
		return !1;
	}
	function Mn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? An : jn, this.isPropagationStopped = jn, this;
		}
		return T(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = An);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = An);
			},
			persist: function() {},
			isPersistent: An
		}), t;
	}
	var Nn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, Pn = Mn(Nn), Fn = T({}, Nn, {
		view: 0,
		detail: 0
	}), In = Mn(Fn), Ln, Rn, zn, Bn = T({}, Fn, {
		screenX: 0,
		screenY: 0,
		clientX: 0,
		clientY: 0,
		pageX: 0,
		pageY: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		getModifierState: Zn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== zn && (zn && e.type === "mousemove" ? (Ln = e.screenX - zn.screenX, Rn = e.screenY - zn.screenY) : Rn = Ln = 0, zn = e), Ln);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : Rn;
		}
	}), Vn = Mn(Bn), Hn = Mn(T({}, Bn, { dataTransfer: 0 })), Un = Mn(T({}, Fn, { relatedTarget: 0 })), Wn = Mn(T({}, Nn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Gn = Mn(T({}, Nn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), Kn = Mn(T({}, Nn, { data: 0 })), qn = {
		Esc: "Escape",
		Spacebar: " ",
		Left: "ArrowLeft",
		Up: "ArrowUp",
		Right: "ArrowRight",
		Down: "ArrowDown",
		Del: "Delete",
		Win: "OS",
		Menu: "ContextMenu",
		Apps: "ContextMenu",
		Scroll: "ScrollLock",
		MozPrintableKey: "Unidentified"
	}, Jn = {
		8: "Backspace",
		9: "Tab",
		12: "Clear",
		13: "Enter",
		16: "Shift",
		17: "Control",
		18: "Alt",
		19: "Pause",
		20: "CapsLock",
		27: "Escape",
		32: " ",
		33: "PageUp",
		34: "PageDown",
		35: "End",
		36: "Home",
		37: "ArrowLeft",
		38: "ArrowUp",
		39: "ArrowRight",
		40: "ArrowDown",
		45: "Insert",
		46: "Delete",
		112: "F1",
		113: "F2",
		114: "F3",
		115: "F4",
		116: "F5",
		117: "F6",
		118: "F7",
		119: "F8",
		120: "F9",
		121: "F10",
		122: "F11",
		123: "F12",
		144: "NumLock",
		145: "ScrollLock",
		224: "Meta"
	}, Yn = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Xn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Yn[e]) ? !!t[e] : !1;
	}
	function Zn() {
		return Xn;
	}
	var Qn = Mn(T({}, Fn, {
		key: function(e) {
			if (e.key) {
				var t = qn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = kn(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Jn[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: Zn,
		charCode: function(e) {
			return e.type === "keypress" ? kn(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? kn(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), $n = Mn(T({}, Bn, {
		pointerId: 0,
		width: 0,
		height: 0,
		pressure: 0,
		tangentialPressure: 0,
		tiltX: 0,
		tiltY: 0,
		twist: 0,
		pointerType: 0,
		isPrimary: 0
	})), er = Mn(T({}, Nn, { submitter: 0 })), tr = Mn(T({}, Fn, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: Zn
	})), nr = Mn(T({}, Nn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), rr = Mn(T({}, Bn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), ir = Mn(T({}, Nn, {
		newState: 0,
		oldState: 0,
		source: 0
	})), ar = [
		9,
		13,
		27,
		32
	], or = Sn && "CompositionEvent" in window, sr = null;
	Sn && "documentMode" in document && (sr = document.documentMode);
	var cr = Sn && "TextEvent" in window && !sr, lr = Sn && (!or || sr && 8 < sr && 11 >= sr), ur = " ", dr = !1;
	function fr(e, t) {
		switch (e) {
			case "keyup": return ar.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function pr(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var U = !1;
	function mr(e, t) {
		switch (e) {
			case "compositionend": return pr(t);
			case "keypress": return t.which === 32 ? (dr = !0, ur) : null;
			case "textInput": return e = t.data, e === ur && dr ? null : e;
			default: return null;
		}
	}
	function hr(e, t) {
		if (U) return e === "compositionend" || !or && fr(e, t) ? (e = On(), Dn = En = Tn = null, U = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return lr && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var gr = {
		color: !0,
		date: !0,
		datetime: !0,
		"datetime-local": !0,
		email: !0,
		month: !0,
		number: !0,
		password: !0,
		range: !0,
		search: !0,
		tel: !0,
		text: !0,
		time: !0,
		url: !0,
		week: !0
	};
	function _r(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!gr[e.type] : t === "textarea";
	}
	function vr(e, t, n, r) {
		gn ? _n ? _n.push(r) : _n = [r] : gn = r, t = qf(t, "onChange"), 0 < t.length && (n = new Pn("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var yr = null, br = null;
	function xr(e) {
		Bf(e, 0);
	}
	function Sr(e) {
		if (Yt(jt(e))) return e;
	}
	function Cr(e, t) {
		if (e === "change") return t;
	}
	var wr = !1;
	if (Sn) {
		var Tr;
		if (Sn) {
			var Er = "oninput" in document;
			if (!Er) {
				var Dr = document.createElement("div");
				Dr.setAttribute("oninput", "return;"), Er = typeof Dr.oninput == "function";
			}
			Tr = Er;
		} else Tr = !1;
		wr = Tr && (!document.documentMode || 9 < document.documentMode);
	}
	function Or() {
		yr && (yr.detachEvent("onpropertychange", kr), br = yr = null);
	}
	function kr(e) {
		if (e.propertyName === "value" && Sr(br)) {
			var t = [];
			vr(t, br, e, hn(e)), bn(xr, t);
		}
	}
	function Ar(e, t, n) {
		e === "focusin" ? (Or(), yr = t, br = n, yr.attachEvent("onpropertychange", kr)) : e === "focusout" && Or();
	}
	function jr(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return Sr(br);
	}
	function Mr(e, t) {
		if (e === "click") return Sr(t);
	}
	function Nr(e, t) {
		if (e === "input" || e === "change") return Sr(t);
	}
	function Pr(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var Fr = typeof Object.is == "function" ? Object.is : Pr;
	function Ir(e, t) {
		if (Fr(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!Pe.call(t, i) || !Fr(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Lr(e) {
		if (e ||= typeof document < "u" ? document : void 0, e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch {
			return e.body;
		}
	}
	function Rr(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function Br(e, t) {
		var n = Rr(e);
		e = 0;
		for (var r; n;) {
			if (n.nodeType === 3) {
				if (r = e + n.textContent.length, e <= t && r >= t) return {
					node: n,
					offset: t - e
				};
				e = r;
			}
			a: {
				for (; n;) {
					if (n.nextSibling) {
						n = n.nextSibling;
						break a;
					}
					n = n.parentNode;
				}
				n = void 0;
			}
			n = Rr(n);
		}
	}
	function Vr(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Vr(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function Hr(e) {
		e = e != null && e.ownerDocument != null && e.ownerDocument.defaultView != null ? e.ownerDocument.defaultView : window;
		for (var t = Lr(e.document); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = Lr(e.document);
		}
		return t;
	}
	function Ur(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	var Wr = Sn && "documentMode" in document && 11 >= document.documentMode, Gr = null, Kr = null, qr = null, Jr = !1;
	function Yr(e, t, n) {
		var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
		Jr || Gr == null || Gr !== Lr(r) || (r = Gr, "selectionStart" in r && Ur(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), qr && Ir(qr, r) || (qr = r, r = qf(Kr, "onSelect"), 0 < r.length && (t = new Pn("onSelect", "select", null, t, n), e.push({
			event: t,
			listeners: r
		}), t.target = Gr)));
	}
	function Xr(e, t) {
		var n = {};
		return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
	}
	var Zr = {
		animationend: Xr("Animation", "AnimationEnd"),
		animationiteration: Xr("Animation", "AnimationIteration"),
		animationstart: Xr("Animation", "AnimationStart"),
		transitionrun: Xr("Transition", "TransitionRun"),
		transitionstart: Xr("Transition", "TransitionStart"),
		transitioncancel: Xr("Transition", "TransitionCancel"),
		transitionend: Xr("Transition", "TransitionEnd")
	}, Qr = {}, $r = {};
	Sn && ($r = document.createElement("div").style, "AnimationEvent" in window || (delete Zr.animationend.animation, delete Zr.animationiteration.animation, delete Zr.animationstart.animation), "TransitionEvent" in window || delete Zr.transitionend.transition);
	function ei(e) {
		if (Qr[e]) return Qr[e];
		if (!Zr[e]) return e;
		var t = Zr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in $r) return Qr[e] = t[n];
		return e;
	}
	var ti = ei("animationend"), ni = ei("animationiteration"), ri = ei("animationstart"), ii = ei("transitionrun"), ai = ei("transitionstart"), oi = ei("transitioncancel"), si = ei("transitionend"), ci = /* @__PURE__ */ new Map(), li = "abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error fullscreenChange fullscreenError gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	li.push("scrollEnd");
	function ui(e, t) {
		ci.set(e, t), It(t, [e]);
	}
	var di = 0;
	function fi(e, t) {
		if (e.name != null && e.name !== "auto") return e.name;
		if (t.autoName !== null) return t.autoName;
		e = Q.identifierPrefix;
		var n = di++;
		return e = "_" + e + "t_" + n.toString(32) + "_", t.autoName = e;
	}
	function pi(e) {
		if (e == null || typeof e == "string") return e;
		var t = null, n = Ed;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var i = e[n[r]];
			if (i != null) {
				if (i === "none") return "none";
				t = t == null ? i : t + (" " + i);
			}
		}
		return t ?? e.default;
	}
	function mi(e, t) {
		return e = pi(e), t = pi(t), t == null ? e === "auto" ? null : e : t === "auto" ? null : t;
	}
	var hi = typeof reportError == "function" ? reportError : function(e) {
		if (typeof window == "object" && typeof window.ErrorEvent == "function") {
			var t = new window.ErrorEvent("error", {
				bubbles: !0,
				cancelable: !0,
				message: typeof e == "object" && e && typeof e.message == "string" ? String(e.message) : String(e),
				error: e
			});
			if (!window.dispatchEvent(t)) return;
		} else if (typeof process == "object" && typeof process.emit == "function") {
			process.emit("uncaughtException", e);
			return;
		}
		console.error(e);
	}, gi = [], _i = 0, vi = 0;
	function yi() {
		for (var e = _i, t = vi = _i = 0; t < e;) {
			var n = gi[t];
			gi[t++] = null;
			var r = gi[t];
			gi[t++] = null;
			var i = gi[t];
			gi[t++] = null;
			var a = gi[t];
			if (gi[t++] = null, r !== null && i !== null) {
				var o = r.pending;
				o === null ? i.next = i : (i.next = o.next, o.next = i), r.pending = i;
			}
			a !== 0 && Ci(n, i, a);
		}
	}
	function bi(e, t, n, r) {
		gi[_i++] = e, gi[_i++] = t, gi[_i++] = n, gi[_i++] = r, vi |= r, e.lanes |= r, e = e.alternate, e !== null && (e.lanes |= r);
	}
	function xi(e, t, n, r) {
		return bi(e, t, n, r), wi(e);
	}
	function Si(e, t) {
		return bi(e, null, null, t), wi(e);
	}
	function Ci(e, t, n) {
		e.lanes |= n;
		var r = e.alternate;
		r !== null && (r.lanes |= n);
		for (var i = !1, a = e.return; a !== null;) a.childLanes |= n, r = a.alternate, r !== null && (r.childLanes |= n), a.tag === 22 && (e = a.stateNode, e === null || e._visibility & 1 || (i = !0)), e = a, a = a.return;
		return e.tag === 3 ? (a = e.stateNode, i && t !== null && (i = 31 - Ze(n), e = a.hiddenUpdates, r = e[i], r === null ? e[i] = [t] : r.push(t), t.lane = n | 536870912), a) : null;
	}
	function wi(e) {
		if (50 < Dd) throw Dd = 0, Od = null, Error(i(185));
		for (var t = e.return; t !== null;) e = t, t = e.return;
		return e.tag === 3 ? e.stateNode : null;
	}
	var Ti = {};
	function Ei(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.refCleanup = this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function Di(e, t, n, r) {
		return new Ei(e, t, n, r);
	}
	function Oi(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function ki(e, t) {
		var n = e.alternate;
		return n === null ? (n = Di(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 1206910976, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n.refCleanup = e.refCleanup, n;
	}
	function Ai(e, t) {
		e.flags &= 1206910978;
		var n = e.alternate;
		return n === null ? (e.childLanes = 0, e.lanes = t, e.child = null, e.subtreeFlags = 0, e.memoizedProps = null, e.memoizedState = null, e.updateQueue = null, e.dependencies = null, e.stateNode = null) : (e.childLanes = n.childLanes, e.lanes = n.lanes, e.child = n.child, e.subtreeFlags = 0, e.deletions = null, e.memoizedProps = n.memoizedProps, e.memoizedState = n.memoizedState, e.updateQueue = n.updateQueue, e.type = n.type, t = n.dependencies, e.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}), e;
	}
	function ji(e, t, n, r, a, o) {
		var s = 0;
		if (r = e, typeof r == "function") Oi(r) && (s = 1);
		else if (typeof r == "string") s = qm(e, n, ye.current) ? 26 : e === "html" || e === "head" || e === "body" ? 27 : 5;
		else a: switch (r) {
			case re: return e = Di(31, n, t, a), e.elementType = re, e.lanes = o, e;
			case k: return Mi(n.children, a, o, t);
			case A:
				s = 8, a |= 24;
				break;
			case j: return e = Di(12, n, t, a | 2), e.elementType = j, e.lanes = o, e;
			case te: return e = Di(13, n, t, a), e.elementType = te, e.lanes = o, e;
			case P: return e = Di(19, n, t, a), e.elementType = P, e.lanes = o, e;
			case ie:
			case oe: return e = a | 32, e = Di(30, n, t, e), e.elementType = oe, e.lanes = o, e.stateNode = {
				autoName: null,
				paired: null,
				clones: null,
				ref: null
			}, e;
			default:
				if (typeof r == "object" && r) switch (r.$$typeof) {
					case N:
						s = 10;
						break a;
					case M:
						s = 9;
						break a;
					case ee:
						s = 11;
						break a;
					case ne:
						s = 14;
						break a;
					case F:
						s = 16, r = null;
						break a;
				}
				s = 29, n = Error(i(130, e === null ? "null" : typeof e, "")), r = null;
		}
		return t = Di(s, n, t, a), t.elementType = e, t.type = r, t.lanes = o, t;
	}
	function Mi(e, t, n, r) {
		return e = Di(7, e, r, t), e.lanes = n, e;
	}
	function Ni(e, t, n) {
		return e = Di(6, e, null, t), e.lanes = n, e;
	}
	function Pi(e) {
		var t = Di(18, null, null, 0);
		return t.stateNode = e, t;
	}
	function Fi(e, t, n) {
		return t = Di(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	var Ii = /* @__PURE__ */ new WeakMap();
	function Li(e, t) {
		if (typeof e == "object" && e) {
			var n = Ii.get(e);
			return n === void 0 ? (t = {
				value: e,
				source: t,
				stack: Ne(t)
			}, Ii.set(e, t), t) : n;
		}
		return {
			value: e,
			source: t,
			stack: Ne(t)
		};
	}
	var Ri = [], zi = 0, Bi = null, Vi = 0, Hi = [], Ui = 0, Wi = null, Gi = 1, Ki = "";
	function qi(e, t) {
		Ri[zi++] = Vi, Ri[zi++] = Bi, Bi = e, Vi = t;
	}
	function Ji(e, t, n) {
		Hi[Ui++] = Gi, Hi[Ui++] = Ki, Hi[Ui++] = Wi, Wi = e;
		var r = Gi;
		e = Ki;
		var i = 32 - Ze(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - Ze(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, Gi = 1 << 32 - Ze(t) + i | n << i | r, Ki = a + e;
		} else Gi = 1 << a | n << i | r, Ki = e;
	}
	function Yi(e) {
		e.return !== null && (qi(e, 1), Ji(e, 1, 0));
	}
	function Xi(e) {
		for (; e === Bi;) Bi = Ri[--zi], Ri[zi] = null, Vi = Ri[--zi], Ri[zi] = null;
		for (; e === Wi;) Wi = Hi[--Ui], Hi[Ui] = null, Ki = Hi[--Ui], Hi[Ui] = null, Gi = Hi[--Ui], Hi[Ui] = null;
	}
	function Zi(e, t) {
		Hi[Ui++] = Gi, Hi[Ui++] = Ki, Hi[Ui++] = Wi, Gi = t.id, Ki = t.overflow, Wi = e;
	}
	var Qi = null, $i = null, W = !1, ea = null, ta = !1, na = Error(i(519));
	function ra(e) {
		throw la(Li(Error(i(418, 1 < arguments.length && arguments[1] !== void 0 && arguments[1] ? "text" : "HTML", "")), e)), na;
	}
	function ia(e) {
		var t = e.stateNode, n = e.type, r = e.memoizedProps;
		switch (t[xt] = e, t[R] = r, n) {
			case "dialog":
				$("cancel", t), $("close", t);
				break;
			case "iframe":
			case "object":
			case "embed":
				$("load", t);
				break;
			case "video":
			case "audio":
				for (n = 0; n < Rf.length; n++) $(Rf[n], t);
				break;
			case "source":
				$("error", t);
				break;
			case "img":
			case "image":
			case "link":
				$("error", t), $("load", t);
				break;
			case "details":
				$("toggle", t);
				break;
			case "input":
				$("invalid", t), $t(t, r.value, r.defaultValue, r.checked, r.defaultChecked, r.type, r.name, !0);
				break;
			case "select":
				$("invalid", t);
				break;
			case "textarea": $("invalid", t), rn(t, r.value, r.defaultValue, r.children);
		}
		n = r.children, typeof n != "string" && typeof n != "number" && typeof n != "bigint" || t.textContent === "" + n || !0 === r.suppressHydrationWarning || $f(t.textContent, n) ? (r.popover != null && ($("beforetoggle", t), $("toggle", t)), r.onScroll != null && $("scroll", t), r.onScrollEnd != null && $("scrollend", t), r.onClick != null && (t.onclick = pn), t = !0) : t = !1, t || ra(e, !0);
	}
	function aa(e) {
		for (Qi = e.return; Qi;) switch (Qi.tag) {
			case 5:
			case 31:
			case 13:
				ta = !1;
				return;
			case 27:
			case 3:
				ta = !0;
				return;
			default: Qi = Qi.return;
		}
	}
	function oa(e) {
		if (e !== Qi) return !1;
		if (!W) return aa(e), W = !0, !1;
		var t = e.tag, n;
		if ((n = t !== 3 && t !== 27) && ((n = t === 5) && (n = e.type, n = n === "form" || n === "button" || pp(e.type, e.memoizedProps)), n = !n), n && $i && ra(e), aa(e), t === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			$i = dm(e);
		} else if (t === 31) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			$i = dm(e);
		} else t === 27 ? (t = $i, Sp(e.type) ? (e = um, um = null, $i = e) : $i = t) : $i = Qi ? lm(e.stateNode.nextSibling) : null;
		return !0;
	}
	function sa() {
		$i = Qi = null, W = !1;
	}
	function ca() {
		var e = ea;
		return e !== null && (Z === null ? Z = e : Z.push.apply(Z, e), ea = null), e;
	}
	function la(e) {
		ea === null ? ea = [e] : ea.push(e);
	}
	var ua = ge(null), da = null, fa = null;
	function pa(e, t, n) {
		ve(ua, t._currentValue), t._currentValue = n;
	}
	function ma(e) {
		e._currentValue = ua.current, _e(ua);
	}
	function ha(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function ga(e, t, n, r) {
		var a = e.child;
		for (a !== null && (a.return = e); a !== null;) {
			var o = a.dependencies;
			if (o !== null) {
				var s = a.child;
				o = o.firstContext;
				a: for (; o !== null;) {
					var c = o;
					o = a;
					for (var l = 0; l < t.length; l++) if (c.context === t[l]) {
						o.lanes |= n, c = o.alternate, c !== null && (c.lanes |= n), ha(o.return, n, e), r || (s = null);
						break a;
					}
					o = c.next;
				}
			} else if (a.tag === 18) {
				if (s = a.return, s === null) throw Error(i(341));
				s.lanes |= n, o = s.alternate, o !== null && (o.lanes |= n), ha(s, n, e), s = null;
			} else a.tag === 13 && a.memoizedState !== null && a.memoizedState.dehydrated === null ? (a.lanes |= n, s = a.alternate, s !== null && (s.lanes |= n), ha(a.return, n, e), s = a.child, s = s === null ? null : s.sibling) : s = a.child;
			if (s !== null) s.return = a;
			else for (s = a; s !== null;) {
				if (s === e) {
					s = null;
					break;
				}
				if (a = s.sibling, a !== null) {
					a.return = s.return, s = a;
					break;
				}
				s = s.return;
			}
			a = s;
		}
	}
	function _a(e, t, n, r) {
		e = null;
		for (var a = t, o = !1; a !== null;) {
			if (!o) {
				if (a.flags & 524288) o = !0;
				else if (a.flags & 262144) break;
			}
			if (a.tag === 10) {
				var s = a.alternate;
				if (s === null) throw Error(i(387));
				if (s = s.memoizedProps, s !== null) {
					var c = a.type;
					Fr(a.pendingProps.value, s.value) || (e === null ? e = [c] : e.push(c));
				}
			} else if (a === Se.current) {
				if (s = a.alternate, s === null) throw Error(i(387));
				s.memoizedState.memoizedState !== a.memoizedState.memoizedState && (e === null ? e = [sh] : e.push(sh));
			}
			a = a.return;
		}
		return e !== null && ga(t, e, n, r), t.flags |= 262144, e !== null;
	}
	function va(e) {
		for (e = e.firstContext; e !== null;) {
			if (!Fr(e.context._currentValue, e.memoizedValue)) return !0;
			e = e.next;
		}
		return !1;
	}
	function ya(e) {
		da = e, fa = null, e = e.dependencies, e !== null && (e.firstContext = null);
	}
	function ba(e) {
		return Sa(da, e);
	}
	function xa(e, t) {
		return da === null && ya(e), Sa(e, t);
	}
	function Sa(e, t) {
		var n = t._currentValue;
		if (t = {
			context: t,
			memoizedValue: n,
			next: null
		}, fa === null) {
			if (e === null) throw Error(i(308));
			fa = t, e.dependencies = {
				lanes: 0,
				firstContext: t
			}, e.flags |= 524288;
		} else fa = fa.next = t;
		return n;
	}
	var Ca = typeof AbortController < "u" ? AbortController : function() {
		var e = [], t = this.signal = {
			aborted: !1,
			addEventListener: function(t, n) {
				e.push(n);
			}
		};
		this.abort = function() {
			t.aborted = !0, e.forEach(function(e) {
				return e();
			});
		};
	}, wa = t.unstable_scheduleCallback, Ta = t.unstable_NormalPriority, Ea = {
		$$typeof: N,
		Consumer: null,
		Provider: null,
		_currentValue: null,
		_currentValue2: null,
		_threadCount: 0
	};
	function Da() {
		return {
			controller: new Ca(),
			data: /* @__PURE__ */ new Map(),
			refCount: 0
		};
	}
	function Oa(e) {
		e.refCount--, e.refCount === 0 && wa(Ta, function() {
			e.controller.abort();
		});
	}
	function ka(e, t) {
		if (e.pendingLanes & 4194048) {
			var n = e.transitionTypes;
			for (n === null && (n = e.transitionTypes = []), e = 0; e < t.length; e++) {
				var r = t[e];
				n.indexOf(r) === -1 && n.push(r);
			}
		}
	}
	var Aa = null;
	function ja(e) {
		var t = e.transitionTypes;
		return e.transitionTypes = null, t;
	}
	var Ma = null, Na = 0, Pa = 0, Fa = null;
	function Ia(e, t) {
		if (Ma === null) {
			var n = Ma = [];
			Na = 0, Pa = Nf(), Fa = {
				status: "pending",
				value: void 0,
				then: function(e) {
					n.push(e);
				}
			};
		}
		return Na++, t.then(La, La), t;
	}
	function La() {
		if (--Na === 0 && (Aa = null, Ma !== null)) {
			Fa !== null && (Fa.status = "fulfilled");
			var e = Ma;
			Ma = null, Pa = 0, Fa = null;
			for (var t = 0; t < e.length; t++) (0, e[t])();
		}
	}
	function Ra(e, t) {
		var n = [], r = {
			status: "pending",
			value: null,
			reason: null,
			then: function(e) {
				n.push(e);
			}
		};
		return e.then(function() {
			r.status = "fulfilled", r.value = t;
			for (var e = 0; e < n.length; e++) (0, n[e])(t);
		}, function(e) {
			for (r.status = "rejected", r.reason = e, e = 0; e < n.length; e++) (0, n[e])(void 0);
		}), r;
	}
	var za = I.S;
	I.S = function(e, t) {
		if (md = ze(), typeof t == "object" && t && typeof t.then == "function" && Ia(e, t), Aa !== null) for (var n = yf; n !== null;) ka(n, Aa), n = n.next;
		if (n = e.types, n !== null) {
			for (var r = yf; r !== null;) ka(r, n), r = r.next;
			if (Pa !== 0) {
				r = Aa, r === null && (r = Aa = []);
				for (var i = 0; i < n.length; i++) {
					var a = n[i];
					r.indexOf(a) === -1 && r.push(a);
				}
			}
		}
		za !== null && za(e, t);
	};
	var Ba = ge(null);
	function Va() {
		var e = Ba.current;
		return e === null ? ed.pooledCache : e;
	}
	function Ha(e, t) {
		t === null ? ve(Ba, Ba.current) : ve(Ba, t.pool);
	}
	function Ua() {
		var e = Va();
		return e === null ? null : {
			parent: Ea._currentValue,
			pool: e
		};
	}
	var Wa = Error(i(460)), Ga = Error(i(474)), Ka = Error(i(542)), qa = { then: function() {} };
	function Ja(e) {
		return e = e.status, e === "fulfilled" || e === "rejected";
	}
	function Ya(e, t, n) {
		switch (n = e[n], n === void 0 ? e.push(t) : n !== t && (t.then(pn, pn), t = n), t.status) {
			case "fulfilled": return t.value;
			case "rejected": throw e = t.reason, $a(e), e === void 0 && !("reason" in t) ? Error(i(600)) : e;
			default:
				if (typeof t.status == "string") t.then(pn, pn);
				else {
					if (e = ed, e !== null && 100 < e.shellSuspendCounter) throw Error(i(482));
					e = t, e.status = "pending", e.then(function(e) {
						if (t.status === "pending") {
							var n = t;
							n.status = "fulfilled", n.value = e;
						}
					}, function(e) {
						if (t.status === "pending") {
							var n = t;
							n.status = "rejected", n.reason = e;
						}
					});
				}
				switch (t.status) {
					case "fulfilled": return t.value;
					case "rejected": throw e = t.reason, $a(e), e;
				}
				throw Za = t, Wa;
		}
	}
	function Xa(e) {
		try {
			var t = e._init;
			return t(e._payload);
		} catch (e) {
			throw typeof e == "object" && e && typeof e.then == "function" ? (Za = e, Wa) : e;
		}
	}
	var Za = null;
	function Qa() {
		if (Za === null) throw Error(i(459));
		var e = Za;
		return Za = null, e;
	}
	function $a(e) {
		if (e === Wa || e === Ka) throw Error(i(483));
	}
	var eo = null, to = 0;
	function no(e) {
		var t = to;
		return to += 1, eo === null && (eo = []), Ya(eo, e, t);
	}
	function ro(e, t) {
		t = t.props.ref, e.ref = t === void 0 ? null : t;
	}
	function io(e, t) {
		throw t.$$typeof === E ? Error(i(525)) : (e = Object.prototype.toString.call(t), Error(i(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e)));
	}
	function ao(e) {
		function t(t, n) {
			if (e) {
				var r = t.deletions;
				r === null ? (t.deletions = [n], t.flags |= 16) : r.push(n);
			}
		}
		function n(n, r) {
			if (!e) return null;
			for (; r !== null;) t(n, r), r = r.sibling;
			return null;
		}
		function r(e) {
			for (var t = /* @__PURE__ */ new Map(); e !== null;) e.key === null ? t.set(e.index, e) : t.set(e.key, e), e = e.sibling;
			return t;
		}
		function a(e, t) {
			return e = ki(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 134217730, n) : (r = r.index, r < n ? (t.flags |= 2, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 134217730), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = Ni(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === k ? (e = d(e, t, n.props.children, r, n.key), ro(e, n), e) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === F && Xa(i) === t.type) ? (t = a(t, n.props), ro(t, n), t.return = e, t) : (t = ji(n.type, n.key, n.props, null, e.mode, r), ro(t, n), t.return = e, t);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = Fi(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = Mi(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number" || typeof t == "bigint") return t = Ni("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case D: return n = ji(t.type, t.key, t.props, null, e.mode, n), ro(n, t), n.return = e, n;
					case O: return t = Fi(t, e.mode, n), t.return = e, t;
					case F: return t = Xa(t), f(e, t, n);
				}
				if (fe(t) || le(t)) return t = Mi(t, e.mode, n, null), t.return = e, t;
				if (typeof t.then == "function") return f(e, no(t), n);
				if (t.$$typeof === N) return f(e, xa(e, t), n);
				io(e, t);
			}
			return null;
		}
		function p(e, t, n, r) {
			var i = t === null ? null : t.key;
			if (typeof n == "string" && n !== "" || typeof n == "number" || typeof n == "bigint") return i === null ? c(e, t, "" + n, r) : null;
			if (typeof n == "object" && n) {
				switch (n.$$typeof) {
					case D: return n.key === i ? l(e, t, n, r) : null;
					case O: return n.key === i ? u(e, t, n, r) : null;
					case F: return n = Xa(n), p(e, t, n, r);
				}
				if (fe(n) || le(n)) return i === null ? d(e, t, n, r, null) : null;
				if (typeof n.then == "function") return p(e, t, no(n), r);
				if (n.$$typeof === N) return p(e, t, xa(e, n), r);
				io(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number" || typeof r == "bigint") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case D: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case O: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case F: return r = Xa(r), m(e, t, n, r, i);
				}
				if (fe(r) || le(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				if (typeof r.then == "function") return m(e, t, n, no(r), i);
				if (r.$$typeof === N) return m(e, t, n, xa(t, r), i);
				io(t, r);
			}
			return null;
		}
		function h(i, a, s, c) {
			for (var l = null, u = null, d = a, h = a = 0, g = null; d !== null && h < s.length; h++) {
				d.index > h ? (g = d, d = null) : g = d.sibling;
				var _ = p(i, d, s[h], c);
				if (_ === null) {
					d === null && (d = g);
					break;
				}
				e && d && _.alternate === null && t(i, d), a = o(_, a, h), u === null ? l = _ : u.sibling = _, u = _, d = g;
			}
			if (h === s.length) return n(i, d), W && qi(i, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(i, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return W && qi(i, h), l;
			}
			for (d = r(d); h < s.length; h++) g = m(d, i, h, s[h], c), g !== null && (e && (_ = g.alternate, _ !== null && d.delete(_.key === null ? h : _.key)), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(i, e);
			}), W && qi(i, h), l;
		}
		function g(a, s, c, l) {
			if (c == null) throw Error(i(151));
			for (var u = null, d = null, h = s, g = s = 0, _ = null, v = c.next(); h !== null && !v.done; g++, v = c.next()) {
				h.index > g ? (_ = h, h = null) : _ = h.sibling;
				var y = p(a, h, v.value, l);
				if (y === null) {
					h === null && (h = _);
					break;
				}
				e && h && y.alternate === null && t(a, h), s = o(y, s, g), d === null ? u = y : d.sibling = y, d = y, h = _;
			}
			if (v.done) return n(a, h), W && qi(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return W && qi(a, g), u;
			}
			for (h = r(h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && (_ = v.alternate, _ !== null && h.delete(_.key === null ? g : _.key)), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), W && qi(a, g), u;
		}
		function _(e, r, o, c) {
			if (typeof o == "object" && o && o.type === k && o.key === null && o.props.ref === void 0 && (o = o.props.children), typeof o == "object" && o) {
				switch (o.$$typeof) {
					case D:
						a: {
							for (var l = o.key; r !== null;) {
								if (r.key === l) {
									if (l = o.type, l === k) {
										if (r.tag === 7) {
											n(e, r.sibling), c = a(r, o.props.children), ro(c, o), c.return = e, e = c;
											break a;
										}
									} else if (r.elementType === l || typeof l == "object" && l && l.$$typeof === F && Xa(l) === r.type) {
										n(e, r.sibling), c = a(r, o.props), ro(c, o), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							o.type === k ? (c = Mi(o.props.children, e.mode, c, o.key), ro(c, o), c.return = e, e = c) : (c = ji(o.type, o.key, o.props, null, e.mode, c), ro(c, o), c.return = e, e = c);
						}
						return s(e);
					case O:
						a: {
							for (l = o.key; r !== null;) {
								if (r.key === l) {
									if (r.tag === 4 && r.stateNode.containerInfo === o.containerInfo && r.stateNode.implementation === o.implementation) {
										n(e, r.sibling), c = a(r, o.children || []), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							c = Fi(o, e.mode, c), c.return = e, e = c;
						}
						return s(e);
					case F: return o = Xa(o), _(e, r, o, c);
				}
				if (fe(o)) return h(e, r, o, c);
				if (le(o)) {
					if (l = le(o), typeof l != "function") throw Error(i(150));
					return o = l.call(o), g(e, r, o, c);
				}
				if (typeof o.then == "function") return _(e, r, no(o), c);
				if (o.$$typeof === N) return _(e, r, xa(e, o), c);
				io(e, o);
			}
			return typeof o == "string" && o !== "" || typeof o == "number" || typeof o == "bigint" ? (o = "" + o, r !== null && r.tag === 6 ? (n(e, r.sibling), c = a(r, o), c.return = e, e = c) : (n(e, r), c = Ni(o, e.mode, c), c.return = e, e = c), s(e)) : n(e, r);
		}
		return function(e, t, n, r) {
			try {
				to = 0;
				var i = _(e, t, n, r);
				return eo = null, i;
			} catch (t) {
				if (t === Wa || t === Ka) throw t;
				var a = Di(29, t, null, e.mode);
				return a.lanes = r, a.return = e, a;
			}
		};
	}
	var oo = ao(!0), so = ao(!1), co = !1;
	function lo(e) {
		e.updateQueue = {
			baseState: e.memoizedState,
			firstBaseUpdate: null,
			lastBaseUpdate: null,
			shared: {
				pending: null,
				lanes: 0,
				hiddenCallbacks: null
			},
			callbacks: null
		};
	}
	function uo(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			callbacks: null
		});
	}
	function fo(e) {
		return {
			lane: e,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function po(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, $u & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, t = wi(e), Ci(e, null, n), t;
		}
		return bi(e, r, t, n), wi(e);
	}
	function mo(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194048)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, mt(e, n);
		}
	}
	function ho(e, t) {
		var n = e.updateQueue, r = e.alternate;
		if (r !== null && (r = r.updateQueue, n === r)) {
			var i = null, a = null;
			if (n = n.firstBaseUpdate, n !== null) {
				do {
					var o = {
						lane: n.lane,
						tag: n.tag,
						payload: n.payload,
						callback: null,
						next: null
					};
					a === null ? i = a = o : a = a.next = o, n = n.next;
				} while (n !== null);
				a === null ? i = a = t : a = a.next = t;
			} else i = a = t;
			n = {
				baseState: r.baseState,
				firstBaseUpdate: i,
				lastBaseUpdate: a,
				shared: r.shared,
				callbacks: r.callbacks
			}, e.updateQueue = n;
			return;
		}
		e = n.lastBaseUpdate, e === null ? n.firstBaseUpdate = t : e.next = t, n.lastBaseUpdate = t;
	}
	var go = !1;
	function _o() {
		if (go) {
			var e = Fa;
			if (e !== null) throw e;
		}
	}
	function vo(e, t, n, r) {
		go = !1;
		var i = e.updateQueue;
		co = !1;
		var a = i.firstBaseUpdate, o = i.lastBaseUpdate, s = i.shared.pending;
		if (s !== null) {
			i.shared.pending = null;
			var c = s, l = c.next;
			c.next = null, o === null ? a = l : o.next = l, o = c;
			var u = e.alternate;
			u !== null && (u = u.updateQueue, s = u.lastBaseUpdate, s !== o && (s === null ? u.firstBaseUpdate = l : s.next = l, u.lastBaseUpdate = c));
		}
		if (a !== null) {
			var d = i.baseState;
			o = 0, u = l = c = null, s = a;
			do {
				var f = s.lane & -536870913, p = f !== s.lane;
				if (p ? (J & f) === f : (r & f) === f) {
					f !== 0 && f === Pa && (go = !0), u !== null && (u = u.next = {
						lane: 0,
						tag: s.tag,
						payload: s.payload,
						callback: null,
						next: null
					});
					a: {
						var m = e, h = s;
						f = t;
						var g = n;
						switch (h.tag) {
							case 1:
								if (m = h.payload, typeof m == "function") {
									d = m.call(g, d, f);
									break a;
								}
								d = m;
								break a;
							case 3: m.flags = m.flags & -65537 | 128;
							case 0:
								if (m = h.payload, f = typeof m == "function" ? m.call(g, d, f) : m, f == null) break a;
								d = T({}, d, f);
								break a;
							case 2: co = !0;
						}
					}
					f = s.callback, f !== null && (e.flags |= 64, p && (e.flags |= 8192), p = i.callbacks, p === null ? i.callbacks = [f] : p.push(f));
				} else p = {
					lane: f,
					tag: s.tag,
					payload: s.payload,
					callback: s.callback,
					next: null
				}, u === null ? (l = u = p, c = d) : u = u.next = p, o |= f;
				if (s = s.next, s === null) {
					if (s = i.shared.pending, s === null) break;
					p = s, s = p.next, p.next = null, i.lastBaseUpdate = p, i.shared.pending = null;
				}
			} while (1);
			u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, a === null && (i.shared.lanes = 0), od |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function yo(e, t) {
		if (typeof e != "function") throw Error(i(191, e));
		e.call(t);
	}
	function bo(e, t) {
		var n = e.callbacks;
		if (n !== null) for (e.callbacks = null, e = 0; e < n.length; e++) yo(n[e], t);
	}
	var xo = ge(null), So = ge(0);
	function Co(e, t) {
		e = id, ve(So, e), ve(xo, t), id = e | t.baseLanes;
	}
	function wo() {
		ve(So, id), ve(xo, xo.current);
	}
	function To() {
		id = So.current, _e(xo), _e(So);
	}
	var Eo = ge(null), Do = null;
	function Oo(e) {
		var t = e.alternate;
		ve(No, No.current & 1), ve(Eo, e), Do === null && (t === null || xo.current !== null || t.memoizedState !== null) && (Do = e);
	}
	function ko(e) {
		ve(No, No.current), ve(Eo, e), Do === null && (Do = e);
	}
	function Ao(e) {
		e.tag === 22 ? (ve(No, No.current), ve(Eo, e), Do === null && (Do = e)) : jo();
	}
	function jo() {
		ve(No, No.current), ve(Eo, Eo.current);
	}
	function Mo(e) {
		_e(Eo), Do === e && (Do = null), _e(No);
	}
	var No = ge(0);
	function Po(e, t) {
		ve(Eo, Eo.current), ve(No, t);
	}
	function Fo(e) {
		_e(No), _e(Eo), Do === e && (Do = null);
	}
	function Io(e) {
		for (var t = e; t !== null;) {
			if (t.tag === 13) {
				var n = t.memoizedState;
				if (n !== null && (n = n.dehydrated, n === null || om(n) || sm(n))) return t;
			} else if (t.tag === 19 && t.memoizedProps.revealOrder !== "independent") {
				if (t.flags & 128) return t;
			} else if (t.child !== null) {
				t.child.return = t, t = t.child;
				continue;
			}
			if (t === e) break;
			for (; t.sibling === null;) {
				if (t.return === null || t.return === e) return null;
				t = t.return;
			}
			t.sibling.return = t.return, t = t.sibling;
		}
		return null;
	}
	var Lo = 0, G = null, Ro = null, zo = null, Bo = !1, Vo = !1, Ho = !1, Uo = 0, Wo = 0, Go = null, Ko = 0;
	function qo() {
		throw Error(i(321));
	}
	function Jo(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!Fr(e[n], t[n])) return !1;
		return !0;
	}
	function Yo(e, t, n, r, i, a) {
		return Lo = a, G = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, I.H = e === null || e.memoizedState === null ? fc : pc, Ho = !1, a = n(r, i), Ho = !1, Vo && (a = Zo(t, n, r, i)), Xo(e), a;
	}
	function Xo(e) {
		I.H = dc;
		var t = Ro !== null && Ro.next !== null;
		if (Lo = 0, zo = Ro = G = null, Bo = !1, Wo = 0, Go = null, t) throw Error(i(300));
		e === null || Ac || (e = e.dependencies, e !== null && va(e) && (Ac = !0));
	}
	function Zo(e, t, n, r) {
		G = e;
		var a = 0;
		do {
			if (Vo && (Go = null), Wo = 0, Vo = !1, 25 <= a) throw Error(i(301));
			if (a += 1, zo = Ro = null, e.updateQueue != null) {
				var o = e.updateQueue;
				o.lastEffect = null, o.events = null, o.stores = null, o.memoCache != null && (o.memoCache.index = 0);
			}
			I.H = mc, o = t(n, r);
		} while (Vo);
		return o;
	}
	function Qo() {
		var e = I.H, t = e.useState()[0];
		return t = typeof t.then == "function" ? as(t) : t, e = e.useState()[0], (Ro === null ? null : Ro.memoizedState) !== e && (G.flags |= 1024), t;
	}
	function $o() {
		var e = Uo !== 0;
		return Uo = 0, e;
	}
	function es(e, t, n) {
		t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~n;
	}
	function ts(e) {
		if (Bo) {
			for (e = e.memoizedState; e !== null;) {
				var t = e.queue;
				t !== null && (t.pending = null), e = e.next;
			}
			Bo = !1;
		}
		Lo = 0, zo = Ro = G = null, Vo = !1, Wo = Uo = 0, Go = null;
	}
	function ns() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return zo === null ? G.memoizedState = zo = e : zo = zo.next = e, zo;
	}
	function rs() {
		if (Ro === null) {
			var e = G.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = Ro.next;
		var t = zo === null ? G.memoizedState : zo.next;
		if (t !== null) zo = t, Ro = e;
		else {
			if (e === null) throw G.alternate === null ? Error(i(467)) : Error(i(310));
			Ro = e, e = {
				memoizedState: Ro.memoizedState,
				baseState: Ro.baseState,
				baseQueue: Ro.baseQueue,
				queue: Ro.queue,
				next: null
			}, zo === null ? G.memoizedState = zo = e : zo = zo.next = e;
		}
		return zo;
	}
	function is() {
		return {
			lastEffect: null,
			events: null,
			stores: null,
			memoCache: null
		};
	}
	function as(e) {
		var t = Wo;
		return Wo += 1, Go === null && (Go = []), e = Ya(Go, e, t), t = G, (zo === null ? t.memoizedState : zo.next) === null && (t = t.alternate, I.H = t === null || t.memoizedState === null ? fc : pc), e;
	}
	function os(e) {
		if (typeof e == "object" && e) {
			if (typeof e.then == "function") return as(e);
			if (e.$$typeof === se) return;
			if (e.$$typeof === N) return ba(e);
		}
		throw Error(i(438, String(e)));
	}
	function ss(e) {
		var t = null, n = G.updateQueue;
		if (n !== null && (t = n.memoCache), t == null) {
			var r = G.alternate;
			r !== null && (r = r.updateQueue, r !== null && (r = r.memoCache, r != null && (t = {
				data: r.data.map(function(e) {
					return e.slice();
				}),
				index: 0
			})));
		}
		if (t ??= {
			data: [],
			index: 0
		}, n === null && (n = is(), G.updateQueue = n), n.memoCache = t, n = t.data[t.index], n === void 0) for (n = t.data[t.index] = Array(e), r = 0; r < e; r++) n[r] = ae;
		return t.index++, n;
	}
	function cs(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function ls(e) {
		return us(rs(), Ro, e);
	}
	function us(e, t, n) {
		var r = e.queue;
		if (r === null) throw Error(i(311));
		r.lastRenderedReducer = n;
		var a = e.baseQueue, o = r.pending;
		if (o !== null) {
			if (a !== null) {
				var s = a.next;
				a.next = o.next, o.next = s;
			}
			t.baseQueue = a = o, r.pending = null;
		}
		if (o = e.baseState, a === null) e.memoizedState = o;
		else {
			t = a.next;
			var c = s = null, l = null, u = t, d = !1;
			do {
				var f = u.lane & -536870913;
				if (f === u.lane ? (Lo & f) === f : (J & f) === f) {
					var p = u.revertLane;
					if (p === 0) l !== null && (l = l.next = {
						lane: 0,
						revertLane: 0,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}), f === Pa && (d = !0);
					else if ((Lo & p) === p) {
						u = u.next, p === Pa && (d = !0);
						continue;
					} else f = {
						lane: 0,
						revertLane: u.revertLane,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}, l === null ? (c = l = f, s = o) : l = l.next = f, G.lanes |= p, od |= p;
					f = u.action, Ho && n(o, f), o = u.hasEagerState ? u.eagerState : n(o, f);
				} else p = {
					lane: f,
					revertLane: u.revertLane,
					gesture: u.gesture,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}, l === null ? (c = l = p, s = o) : l = l.next = p, G.lanes |= f, od |= f;
				u = u.next;
			} while (u !== null && u !== t);
			if (l === null ? s = o : l.next = c, !Fr(o, e.memoizedState) && (Ac = !0, d && (n = Fa, n !== null))) throw n;
			e.memoizedState = o, e.baseState = s, e.baseQueue = l, r.lastRenderedState = o;
		}
		return a === null && (r.lanes = 0), [e.memoizedState, r.dispatch];
	}
	function ds(e) {
		var t = rs(), n = t.queue;
		if (n === null) throw Error(i(311));
		n.lastRenderedReducer = e;
		var r = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			Fr(o, t.memoizedState) || (Ac = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, r];
	}
	function fs(e, t, n) {
		var r = G, a = rs(), o = W;
		if (o) {
			if (n === void 0) throw Error(i(407));
			n = n();
		} else n = t();
		var s = !Fr((Ro || a).memoizedState, n);
		if (s && (a.memoizedState = n, Ac = !0), a = a.queue, Ls(hs.bind(null, r, a, e), [e]), e = a.getSnapshot !== t || s || zo !== null && !!(zo.memoizedState.tag & 1), Ms(e ? 9 : 8, { destroy: void 0 }, ms.bind(null, r, a, n, t), null), e) {
			if (r.flags |= 2048, ed === null) throw Error(i(349));
			o || Lo & 127 || ps(r, t, n);
		}
		return n;
	}
	function ps(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = G.updateQueue, t === null ? (t = is(), G.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function ms(e, t, n, r) {
		t.value = n, t.getSnapshot = r, gs(t) && _s(e);
	}
	function hs(e, t, n) {
		return n(function() {
			gs(t) && _s(e);
		});
	}
	function gs(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !Fr(e, n);
		} catch {
			return !0;
		}
	}
	function _s(e) {
		var t = Si(e, 2);
		t !== null && Md(t, e, 2);
	}
	function vs(e) {
		var t = ns();
		if (typeof e == "function") {
			var n = e;
			if (e = n(), Ho) {
				Xe(!0);
				try {
					n();
				} finally {
					Xe(!1);
				}
			}
		}
		return t.memoizedState = t.baseState = e, t.queue = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: cs,
			lastRenderedState: e
		}, t;
	}
	function ys(e, t, n, r) {
		return e.baseState = n, us(e, Ro, typeof r == "function" ? r : cs);
	}
	function bs(e, t, n, r, a) {
		if (cc(e)) throw Error(i(485));
		if (e = t.action, e !== null) {
			var o = {
				payload: a,
				action: e,
				next: null,
				isTransition: !0,
				status: "pending",
				value: null,
				reason: null,
				listeners: [],
				then: function(e) {
					o.listeners.push(e);
				}
			};
			I.T === null ? o.isTransition = !1 : n(!0), r(o), n = t.pending, n === null ? (o.next = t.pending = o, xs(t, o)) : (o.next = n.next, t.pending = n.next = o);
		}
	}
	function xs(e, t) {
		var n = t.action, r = t.payload, i = e.state;
		if (t.isTransition) {
			var a = I.T, o = {};
			o.types = a === null ? null : a.types, I.T = o;
			try {
				var s = n(i, r), c = I.S;
				c !== null && c(o, s), Ss(e, t, s);
			} catch (n) {
				ws(e, t, n);
			} finally {
				a !== null && o.types !== null && (a.types = o.types), I.T = a;
			}
		} else try {
			a = n(i, r), Ss(e, t, a);
		} catch (n) {
			ws(e, t, n);
		}
	}
	function Ss(e, t, n) {
		typeof n == "object" && n && typeof n.then == "function" ? n.then(function(n) {
			Cs(e, t, n);
		}, function(n) {
			return ws(e, t, n);
		}) : Cs(e, t, n);
	}
	function Cs(e, t, n) {
		t.status = "fulfilled", t.value = n, Ts(t), e.state = n, t = e.pending, t !== null && (n = t.next, n === t ? e.pending = null : (n = n.next, t.next = n, xs(e, n)));
	}
	function ws(e, t, n) {
		var r = e.pending;
		if (e.pending = null, r !== null) {
			r = r.next;
			do
				t.status = "rejected", t.reason = n, Ts(t), t = t.next;
			while (t !== r);
		}
		e.action = null;
	}
	function Ts(e) {
		e = e.listeners;
		for (var t = 0; t < e.length; t++) (0, e[t])();
	}
	function Es(e, t) {
		return t;
	}
	function Ds(e, t) {
		if (W) {
			var n = ed.formState;
			if (n !== null) {
				a: {
					var r = G;
					if (W) {
						if ($i) {
							b: {
								for (var i = $i, a = ta; i.nodeType !== 8;) {
									if (!a) {
										i = null;
										break b;
									}
									if (i = lm(i.nextSibling), i === null) {
										i = null;
										break b;
									}
								}
								a = i.data, i = a === "F!" || a === "F" ? i : null;
							}
							if (i) {
								$i = lm(i.nextSibling), r = i.data === "F!";
								break a;
							}
						}
						ra(r);
					}
					r = !1;
				}
				r && (t = n[0]);
			}
		}
		return n = ns(), n.memoizedState = n.baseState = t, r = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Es,
			lastRenderedState: t
		}, n.queue = r, n = ac.bind(null, G, r), r.dispatch = n, r = vs(!1), a = sc.bind(null, G, !1, r.queue), r = ns(), i = {
			state: t,
			dispatch: null,
			action: e,
			pending: null
		}, r.queue = i, n = bs.bind(null, G, i, a, n), i.dispatch = n, r.memoizedState = e, [
			t,
			n,
			!1
		];
	}
	function Os(e) {
		return ks(rs(), Ro, e);
	}
	function ks(e, t, n) {
		if (t = us(e, t, Es)[0], e = ls(cs)[0], typeof t == "object" && t && typeof t.then == "function") try {
			var r = as(t);
		} catch (e) {
			throw e === Wa ? Ka : e;
		}
		else r = t;
		t = rs();
		var i = t.queue, a = i.dispatch;
		return n !== t.memoizedState && (G.flags |= 2048, Ms(9, { destroy: void 0 }, As.bind(null, i, n), null)), [
			r,
			a,
			e
		];
	}
	function As(e, t) {
		e.action = t;
	}
	function js(e) {
		var t = rs(), n = Ro;
		if (n !== null) return ks(t, n, e);
		rs(), t = t.memoizedState, n = rs();
		var r = n.queue.dispatch;
		return n.memoizedState = e, [
			t,
			r,
			!1
		];
	}
	function Ms(e, t, n, r) {
		return e = {
			tag: e,
			create: n,
			deps: r,
			inst: t,
			next: null
		}, t = G.updateQueue, t === null && (t = is(), G.updateQueue = t), n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e), e;
	}
	function Ns() {
		return rs().memoizedState;
	}
	function Ps(e, t, n, r) {
		var i = ns();
		G.flags |= e, i.memoizedState = Ms(1 | t, { destroy: void 0 }, n, r === void 0 ? null : r);
	}
	function Fs(e, t, n, r) {
		var i = rs();
		r = r === void 0 ? null : r;
		var a = i.memoizedState.inst;
		Ro !== null && r !== null && Jo(r, Ro.memoizedState.deps) ? i.memoizedState = Ms(t, a, n, r) : (G.flags |= e, i.memoizedState = Ms(1 | t, a, n, r));
	}
	function Is(e, t) {
		Ps(8390656, 8, e, t);
	}
	function Ls(e, t) {
		Fs(2048, 8, e, t);
	}
	function Rs(e) {
		G.flags |= 4;
		var t = G.updateQueue;
		if (t === null) t = is(), G.updateQueue = t, t.events = [e];
		else {
			var n = t.events;
			n === null ? t.events = [e] : n.push(e);
		}
	}
	function zs(e) {
		var t = rs().memoizedState;
		return Rs({
			ref: t,
			nextImpl: e
		}), function() {
			if ($u & 2) throw Error(i(440));
			return t.impl.apply(void 0, arguments);
		};
	}
	function Bs(e, t) {
		return Fs(4, 2, e, t);
	}
	function Vs(e, t) {
		return Fs(4, 4, e, t);
	}
	function Hs(e, t) {
		if (typeof t == "function") {
			e = e();
			var n = t(e);
			return function() {
				typeof n == "function" ? n() : t(null);
			};
		}
		if (t != null) return e = e(), t.current = e, function() {
			t.current = null;
		};
	}
	function Us(e, t, n) {
		n = n == null ? null : n.concat([e]), Fs(4, 4, Hs.bind(null, t, e), n);
	}
	function Ws() {}
	function Gs(e, t) {
		var n = rs();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return t !== null && Jo(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function Ks(e, t) {
		var n = rs();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		if (t !== null && Jo(t, r[1])) return r[0];
		if (r = e(), Ho) {
			Xe(!0);
			try {
				e();
			} finally {
				Xe(!1);
			}
		}
		return n.memoizedState = [r, t], r;
	}
	function qs(e, t, n) {
		return n === void 0 || Lo & 1073741824 && !(J & 261930) ? e.memoizedState = t : (e.memoizedState = n, e = Ad(), G.lanes |= e, od |= e, n);
	}
	function Js(e, t, n, r) {
		return Fr(n, t) ? n : xo.current === null ? !(Lo & 106) || Lo & 1073741824 && !(J & 261930) ? (Ac = !0, e.memoizedState = n) : (e = Ad(), G.lanes |= e, od |= e, t) : (e = qs(e, n, r), Fr(e, t) || (Ac = !0), e);
	}
	function Ys(e, t, n, r, i) {
		var a = L.p;
		L.p = a !== 0 && 8 > a ? a : 8;
		var o = I.T, s = {};
		s.types = o === null ? null : o.types, I.T = s, sc(e, !1, t, n);
		try {
			var c = i(), l = I.S;
			l !== null && l(s, c), typeof c == "object" && c && typeof c.then == "function" ? oc(e, t, Ra(c, r), kd(e)) : oc(e, t, r, kd(e));
		} catch (n) {
			oc(e, t, {
				then: function() {},
				status: "rejected",
				reason: n
			}, kd());
		} finally {
			L.p = a, o !== null && s.types !== null && (o.types = s.types), I.T = o;
		}
	}
	function Xs() {}
	function Zs(e, t, n, r) {
		if (e.tag !== 5) throw Error(i(476));
		var a = Qs(e).queue;
		Ys(e, a, t, pe, n === null ? Xs : function() {
			return $s(e), n(r);
		});
	}
	function Qs(e) {
		var t = e.memoizedState;
		if (t !== null) return t;
		t = {
			memoizedState: pe,
			baseState: pe,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: cs,
				lastRenderedState: pe
			},
			next: null
		};
		var n = {};
		return t.next = {
			memoizedState: n,
			baseState: n,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: cs,
				lastRenderedState: n
			},
			next: null
		}, e.memoizedState = t, e = e.alternate, e !== null && (e.memoizedState = t), t;
	}
	function $s(e) {
		var t = Qs(e);
		t.next === null && (t = e.alternate.memoizedState), oc(e, t.next.queue, {}, kd());
	}
	function ec() {
		return ba(sh);
	}
	function tc() {
		return rs().memoizedState;
	}
	function nc() {
		return rs().memoizedState;
	}
	function rc(e) {
		for (var t = e.return; t !== null;) {
			switch (t.tag) {
				case 24:
				case 3:
					var n = kd();
					e = fo(n);
					var r = po(t, e, n);
					r !== null && (Md(r, t, n), mo(r, t, n)), t = { cache: Da() }, e.payload = t;
					return;
			}
			t = t.return;
		}
	}
	function ic(e, t, n) {
		var r = kd();
		n = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, cc(e) ? lc(t, n) : (n = xi(e, t, n, r), n !== null && (Md(n, e, r), uc(n, t, r)));
	}
	function ac(e, t, n) {
		oc(e, t, n, kd());
	}
	function oc(e, t, n, r) {
		var i = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (cc(e)) lc(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, Fr(s, o)) return bi(e, t, i, 0), ed === null && yi(), !1;
			} catch {}
			if (n = xi(e, t, i, r), n !== null) return Md(n, e, r), uc(n, t, r), !0;
		}
		return !1;
	}
	function sc(e, t, n, r) {
		if (r = {
			lane: 2,
			revertLane: Nf(),
			gesture: null,
			action: r,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, cc(e)) {
			if (t) throw Error(i(479));
		} else t = xi(e, n, r, 2), t !== null && Md(t, e, 2);
	}
	function cc(e) {
		var t = e.alternate;
		return e === G || t !== null && t === G;
	}
	function lc(e, t) {
		Vo = Bo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function uc(e, t, n) {
		if (n & 4194048) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, mt(e, n);
		}
	}
	var dc = {
		readContext: ba,
		use: os,
		useCallback: qo,
		useContext: qo,
		useEffect: qo,
		useImperativeHandle: qo,
		useLayoutEffect: qo,
		useInsertionEffect: qo,
		useMemo: qo,
		useReducer: qo,
		useRef: qo,
		useState: qo,
		useDebugValue: qo,
		useDeferredValue: qo,
		useTransition: qo,
		useSyncExternalStore: qo,
		useId: qo,
		useHostTransitionStatus: qo,
		useFormState: qo,
		useActionState: qo,
		useOptimistic: qo,
		useMemoCache: qo,
		useCacheRefresh: qo,
		useEffectEvent: qo
	}, fc = {
		readContext: ba,
		use: os,
		useCallback: function(e, t) {
			return ns().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: ba,
		useEffect: Is,
		useImperativeHandle: function(e, t, n) {
			n = n == null ? null : n.concat([e]), Ps(4194308, 4, Hs.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return Ps(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			Ps(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = ns();
			t = t === void 0 ? null : t;
			var r = e();
			if (Ho) {
				Xe(!0);
				try {
					e();
				} finally {
					Xe(!1);
				}
			}
			return n.memoizedState = [r, t], r;
		},
		useReducer: function(e, t, n) {
			var r = ns();
			if (n !== void 0) {
				var i = n(t);
				if (Ho) {
					Xe(!0);
					try {
						n(t);
					} finally {
						Xe(!1);
					}
				}
			} else i = t;
			return r.memoizedState = r.baseState = i, e = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: i
			}, r.queue = e, e = e.dispatch = ic.bind(null, G, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = ns();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: function(e) {
			e = vs(e);
			var t = e.queue, n = ac.bind(null, G, t);
			return t.dispatch = n, [e.memoizedState, n];
		},
		useDebugValue: Ws,
		useDeferredValue: function(e, t) {
			return qs(ns(), e, t);
		},
		useTransition: function() {
			var e = vs(!1);
			return e = Ys.bind(null, G, e.queue, !0, !1), ns().memoizedState = e, [!1, e];
		},
		useSyncExternalStore: function(e, t, n) {
			var r = G, a = ns();
			if (W) {
				if (n === void 0) throw Error(i(407));
				n = n();
			} else {
				if (n = t(), ed === null) throw Error(i(349));
				J & 127 || ps(r, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, Is(hs.bind(null, r, o, e), [e]), r.flags |= 2048, Ms(9, { destroy: void 0 }, ms.bind(null, r, o, n, t), null), n;
		},
		useId: function() {
			var e = ns(), t = ed.identifierPrefix;
			if (W) {
				var n = Ki, r = Gi;
				n = (r & ~(1 << 32 - Ze(r) - 1)).toString(32) + n, t = "_" + t + "R_" + n, n = Uo++, 0 < n && (t += "H" + n.toString(32)), t += "_";
			} else n = Ko++, t = "_" + t + "r_" + n.toString(32) + "_";
			return e.memoizedState = t;
		},
		useHostTransitionStatus: ec,
		useFormState: Ds,
		useActionState: Ds,
		useOptimistic: function(e) {
			var t = ns();
			t.memoizedState = t.baseState = e;
			var n = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: null,
				lastRenderedState: null
			};
			return t.queue = n, t = sc.bind(null, G, !0, n), n.dispatch = t, [e, t];
		},
		useMemoCache: ss,
		useCacheRefresh: function() {
			return ns().memoizedState = rc.bind(null, G);
		},
		useEffectEvent: function(e) {
			var t = ns(), n = { impl: e };
			return t.memoizedState = n, function() {
				if ($u & 2) throw Error(i(440));
				return n.impl.apply(void 0, arguments);
			};
		}
	}, pc = {
		readContext: ba,
		use: os,
		useCallback: Gs,
		useContext: ba,
		useEffect: Ls,
		useImperativeHandle: Us,
		useInsertionEffect: Bs,
		useLayoutEffect: Vs,
		useMemo: Ks,
		useReducer: ls,
		useRef: Ns,
		useState: function() {
			return ls(cs);
		},
		useDebugValue: Ws,
		useDeferredValue: function(e, t) {
			return Js(rs(), Ro.memoizedState, e, t);
		},
		useTransition: function() {
			var e = ls(cs)[0], t = rs().memoizedState;
			return [typeof e == "boolean" ? e : as(e), t];
		},
		useSyncExternalStore: fs,
		useId: tc,
		useHostTransitionStatus: ec,
		useFormState: Os,
		useActionState: Os,
		useOptimistic: function(e, t) {
			return ys(rs(), Ro, e, t);
		},
		useMemoCache: ss,
		useCacheRefresh: nc,
		useEffectEvent: zs
	}, mc = {
		readContext: ba,
		use: os,
		useCallback: Gs,
		useContext: ba,
		useEffect: Ls,
		useImperativeHandle: Us,
		useInsertionEffect: Bs,
		useLayoutEffect: Vs,
		useMemo: Ks,
		useReducer: ds,
		useRef: Ns,
		useState: function() {
			return ds(cs);
		},
		useDebugValue: Ws,
		useDeferredValue: function(e, t) {
			var n = rs();
			return Ro === null ? qs(n, e, t) : Js(n, Ro.memoizedState, e, t);
		},
		useTransition: function() {
			var e = ds(cs)[0], t = rs().memoizedState;
			return [typeof e == "boolean" ? e : as(e), t];
		},
		useSyncExternalStore: fs,
		useId: tc,
		useHostTransitionStatus: ec,
		useFormState: js,
		useActionState: js,
		useOptimistic: function(e, t) {
			var n = rs();
			return Ro === null ? (n.baseState = e, [e, n.queue.dispatch]) : ys(n, Ro, e, t);
		},
		useMemoCache: ss,
		useCacheRefresh: nc,
		useEffectEvent: zs
	};
	function hc(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : T({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var gc = {
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = kd(), i = fo(r);
			i.payload = t, n != null && (i.callback = n), t = po(e, i, r), t !== null && (Md(t, e, r), mo(t, e, r));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = kd(), i = fo(r);
			i.tag = 1, i.payload = t, n != null && (i.callback = n), t = po(e, i, r), t !== null && (Md(t, e, r), mo(t, e, r));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = kd(), r = fo(n);
			r.tag = 2, t != null && (r.callback = t), t = po(e, r, n), t !== null && (Md(t, e, n), mo(t, e, n));
		}
	};
	function _c(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Ir(n, r) || !Ir(i, a) : !0;
	}
	function vc(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && gc.enqueueReplaceState(t, t.state, null);
	}
	function yc(e, t) {
		var n = t;
		if ("ref" in t) for (var r in n = {}, t) r !== "ref" && (n[r] = t[r]);
		if (e = e.defaultProps) for (var i in n === t && (n = T({}, n)), e) n[i] === void 0 && (n[i] = e[i]);
		return n;
	}
	function bc(e) {
		hi(e);
	}
	function xc(e) {
		console.error(e);
	}
	function Sc(e) {
		hi(e);
	}
	function Cc(e, t) {
		try {
			var n = e.onUncaughtError;
			n(t.value, { componentStack: t.stack });
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function wc(e, t, n) {
		try {
			var r = e.onCaughtError;
			r(n.value, {
				componentStack: n.stack,
				errorBoundary: t.tag === 1 ? t.stateNode : null
			});
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function Tc(e, t, n) {
		return n = fo(n), n.tag = 3, n.payload = { element: null }, n.callback = function() {
			Cc(e, t);
		}, n;
	}
	function Ec(e) {
		return e = fo(e), e.tag = 3, e;
	}
	function Dc(e, t, n, r) {
		var i = n.type.getDerivedStateFromError;
		if (typeof i == "function") {
			var a = r.value;
			e.payload = function() {
				return i(a);
			}, e.callback = function() {
				wc(t, n, r);
			};
		}
		var o = n.stateNode;
		o !== null && typeof o.componentDidCatch == "function" && (e.callback = function() {
			wc(t, n, r), typeof i != "function" && (_d === null ? _d = /* @__PURE__ */ new Set([this]) : _d.add(this));
			var e = r.stack;
			this.componentDidCatch(r.value, { componentStack: e === null ? "" : e });
		});
	}
	function Oc(e, t, n, r, a) {
		if (n.flags |= 32768, typeof r == "object" && r && typeof r.then == "function") {
			if (t = n.alternate, t !== null && _a(t, n, a, !0), n = Eo.current, n !== null) {
				switch (n.tag) {
					case 31:
					case 13:
					case 19: return Do === null ? Wd() : n.alternate === null && ad === 0 && (ad = 3), n.flags &= -257, n.flags |= 65536, n.lanes = a, r === qa ? n.flags |= 16384 : (t = n.updateQueue, t === null ? n.updateQueue = /* @__PURE__ */ new Set([r]) : t.add(r), pf(e, r, a)), !1;
					case 22: return n.flags |= 65536, r === qa ? n.flags |= 16384 : (t = n.updateQueue, t === null ? (t = {
						transitions: null,
						markerInstances: null,
						retryQueue: /* @__PURE__ */ new Set([r])
					}, n.updateQueue = t) : (n = t.retryQueue, n === null ? t.retryQueue = /* @__PURE__ */ new Set([r]) : n.add(r)), pf(e, r, a)), !1;
				}
				throw Error(i(435, n.tag));
			}
			return pf(e, r, a), Wd(), !1;
		}
		if (W) return t = Eo.current, t === null ? (r !== na && (t = Error(i(423), { cause: r }), la(Li(t, n))), e = e.current.alternate, e.flags |= 65536, a &= -a, e.lanes |= a, r = Li(r, n), a = Tc(e.stateNode, r, a), ho(e, a), ad !== 4 && (ad = 2)) : (!(t.flags & 65536) && (t.flags |= 256), t.flags |= 65536, t.lanes = a, r !== na && (e = Error(i(422), { cause: r }), la(Li(e, n)))), !1;
		var o = Error(i(520), { cause: r });
		if (o = Li(o, n), dd === null ? dd = [o] : dd.push(o), ad !== 4 && (ad = 2), t === null) return !0;
		r = Li(r, n), n = t;
		do {
			switch (n.tag) {
				case 3: return n.flags |= 65536, e = a & -a, n.lanes |= e, e = Tc(n.stateNode, r, e), ho(n, e), !1;
				case 1:
					if (t = n.type, o = n.stateNode, !(n.flags & 128) && (typeof t.getDerivedStateFromError == "function" || o !== null && typeof o.componentDidCatch == "function" && (_d === null || !_d.has(o)))) return n.flags |= 65536, a &= -a, n.lanes |= a, a = Ec(a), Dc(a, e, n, r), ho(n, a), !1;
					break;
				case 22: if (n.memoizedState !== null) return n.flags |= 65536, !1;
			}
			n = n.return;
		} while (n !== null);
		return !1;
	}
	var kc = Error(i(461)), Ac = !1;
	function jc(e, t, n, r) {
		t.child = e === null ? so(t, null, n, r) : oo(t, e.child, n, r);
	}
	function Mc(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		if ("ref" in r) {
			var o = {};
			for (var s in r) s !== "ref" && (o[s] = r[s]);
		} else o = r;
		return ya(t), r = Yo(e, t, n, o, a, i), s = $o(), e !== null && !Ac ? (es(e, t, i), ol(e, t, i)) : (W && s && Yi(t), t.flags |= 1, jc(e, t, r, i), t.child);
	}
	function Nc(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !Oi(a) && a.defaultProps === void 0 && n.compare === null ? (t.tag = 15, t.type = a, Pc(e, t, a, r, i)) : (e = ji(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, !sl(e, i)) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Ir : n, n(o, r) && e.ref === t.ref) return ol(e, t, i);
		}
		return t.flags |= 1, e = ki(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function Pc(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Ir(a, r) && e.ref === t.ref) {
				if (Ac = !1, t.pendingProps = r = a, sl(e, i)) e.flags & 131072 && (Ac = !0);
				else return t.lanes = e.lanes, ol(e, t, i);
			}
		}
		return Hc(e, t, n, r, i);
	}
	function Fc(e, t, n, r) {
		var i = r.children, a = e === null ? null : e.memoizedState;
		if (e === null && t.stateNode === null && (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), r.mode === "hidden") {
			if (t.flags & 128) {
				if (a = a === null ? n : a.baseLanes | n, e !== null) {
					for (r = t.child = e.child, i = 0; r !== null;) i = i | r.lanes | r.childLanes, r = r.sibling;
					r = i & ~a;
				} else r = 0, t.child = null;
				return Lc(e, t, a, n, r);
			}
			if (n & 536870912) t.memoizedState = {
				baseLanes: 0,
				cachePool: null
			}, e !== null && Ha(t, a === null ? null : a.cachePool), a === null ? wo() : Co(t, a), Ao(t);
			else return r = t.lanes = 536870912, Lc(e, t, a === null ? n : a.baseLanes | n, n, r);
		} else a === null ? (e !== null && Ha(t, null), wo(), jo()) : (Ha(t, a.cachePool), Co(t, a), jo(), t.memoizedState = null);
		return jc(e, t, i, n), t.child;
	}
	function Ic(e, t) {
		return e !== null && e.tag === 22 || t.stateNode !== null || (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), t.sibling;
	}
	function Lc(e, t, n, r, i) {
		var a = Va();
		return a = a === null ? null : {
			parent: Ea._currentValue,
			pool: a
		}, t.memoizedState = {
			baseLanes: n,
			cachePool: a
		}, e !== null && Ha(t, null), wo(), Ao(t), e !== null && _a(e, t, r, !0), t.childLanes = i, null;
	}
	function Rc(e, t) {
		return t = Zc({
			mode: t.mode,
			children: t.children
		}, e.mode), t.ref = e.ref, e.child = t, t.return = e, t;
	}
	function zc(e, t, n) {
		return oo(t, e.child, null, n), e = Rc(t, t.pendingProps), e.flags |= 2, Mo(t), t.memoizedState = null, e;
	}
	function Bc(e, t, n) {
		var r = t.pendingProps, a = !!(t.flags & 128);
		if (t.flags &= -129, e === null) {
			if (W) {
				if (r.mode === "hidden") return e = Rc(t, r), t.lanes = 536870912, e.memoizedState = {
					baseLanes: 0,
					cachePool: null
				}, Ic(null, e);
				if (ko(t), (e = $i) ? (e = am(e, ta), e = e !== null && e.data === "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Wi === null ? null : {
						id: Gi,
						overflow: Ki
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = Pi(e), n.return = t, t.child = n, Qi = t, $i = null)) : e = null, e === null) throw ra(t);
				return t.lanes = 536870912, null;
			}
			return Rc(t, r);
		}
		var o = e.memoizedState;
		if (o !== null) {
			var s = o.dehydrated;
			if (ko(t), a) {
				if (t.flags & 256) t.flags &= -257, t = zc(e, t, n);
				else if (t.memoizedState !== null) t.child = e.child, t.flags |= 128, t = null;
				else throw Error(i(558));
			} else if (Ac || _a(e, t, n, !1), a = (n & e.childLanes) !== 0, Ac || a) {
				if (xo.current === null) {
					if (r = ed, r !== null && (s = ht(r, n), s !== 0 && s !== o.retryLane)) throw o.retryLane = s, Si(e, s), Md(r, e, s), kc;
					Wd();
				}
				t = zc(e, t, n);
			} else e = o.treeContext, $i = lm(s.nextSibling), Qi = t, W = !0, ea = null, ta = !1, e !== null && Zi(t, e), t = Rc(t, r), t.flags |= 134221824;
			return t;
		}
		return e = ki(e.child, {
			mode: r.mode,
			children: r.children
		}), e.ref = t.ref, t.child = e, e.return = t, e;
	}
	function Vc(e, t) {
		var n = t.ref;
		if (n === null) e !== null && e.ref !== null && (t.flags |= 4194816);
		else {
			if (typeof n != "function" && typeof n != "object") throw Error(i(284));
			(e === null || e.ref !== n) && (t.flags |= 4194816);
		}
	}
	function Hc(e, t, n, r, i) {
		return ya(t), n = Yo(e, t, n, r, void 0, i), r = $o(), e !== null && !Ac ? (es(e, t, i), ol(e, t, i)) : (W && r && Yi(t), t.flags |= 1, jc(e, t, n, i), t.child);
	}
	function Uc(e, t, n, r, i, a) {
		return ya(t), t.updateQueue = null, n = Zo(t, r, n, i), Xo(e), r = $o(), e !== null && !Ac ? (es(e, t, a), ol(e, t, a)) : (W && r && Yi(t), t.flags |= 1, jc(e, t, n, a), t.child);
	}
	function Wc(e, t, n, r, i) {
		if (ya(t), t.stateNode === null) {
			var a = Ti, o = n.contextType;
			typeof o == "object" && o && (a = ba(o)), a = new n(r, a), t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, a.updater = gc, t.stateNode = a, a._reactInternals = t, a = t.stateNode, a.props = r, a.state = t.memoizedState, a.refs = {}, lo(t), o = n.contextType, a.context = typeof o == "object" && o ? ba(o) : Ti, a.state = t.memoizedState, o = n.getDerivedStateFromProps, typeof o == "function" && (hc(t, n, o, r), a.state = t.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof a.getSnapshotBeforeUpdate == "function" || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (o = a.state, typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount(), o !== a.state && gc.enqueueReplaceState(a, a.state, null), vo(t, r, a, i), _o(), a.state = t.memoizedState), typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !0;
		} else if (e === null) {
			a = t.stateNode;
			var s = t.memoizedProps, c = yc(n, s);
			a.props = c;
			var l = a.context, u = n.contextType;
			o = Ti, typeof u == "object" && u && (o = ba(u));
			var d = n.getDerivedStateFromProps;
			u = typeof d == "function" || typeof a.getSnapshotBeforeUpdate == "function", s = t.pendingProps !== s, u || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (s || l !== o) && vc(t, a, r, o), co = !1;
			var f = t.memoizedState;
			a.state = f, vo(t, r, a, i), _o(), l = t.memoizedState, s || f !== l || co ? (typeof d == "function" && (hc(t, n, d, r), l = t.memoizedState), (c = co || _c(t, n, c, r, f, l, o)) ? (u || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount()), typeof a.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = l), a.props = r, a.state = l, a.context = o, r = c) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			a = t.stateNode, uo(e, t), o = t.memoizedProps, u = yc(n, o), a.props = u, d = t.pendingProps, f = a.context, l = n.contextType, c = Ti, typeof l == "object" && l && (c = ba(l)), s = n.getDerivedStateFromProps, (l = typeof s == "function" || typeof a.getSnapshotBeforeUpdate == "function") || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (o !== d || f !== c) && vc(t, a, r, c), co = !1, f = t.memoizedState, a.state = f, vo(t, r, a, i), _o();
			var p = t.memoizedState;
			o !== d || f !== p || co || e !== null && e.dependencies !== null && va(e.dependencies) ? (typeof s == "function" && (hc(t, n, s, r), p = t.memoizedState), (u = co || _c(t, n, u, r, f, p, c) || e !== null && e.dependencies !== null && va(e.dependencies)) ? (l || typeof a.UNSAFE_componentWillUpdate != "function" && typeof a.componentWillUpdate != "function" || (typeof a.componentWillUpdate == "function" && a.componentWillUpdate(r, p, c), typeof a.UNSAFE_componentWillUpdate == "function" && a.UNSAFE_componentWillUpdate(r, p, c)), typeof a.componentDidUpdate == "function" && (t.flags |= 4), typeof a.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = p), a.props = r, a.state = p, a.context = c, r = u) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return a = r, Vc(e, t), r = !!(t.flags & 128), a || r ? (a = t.stateNode, n = r && typeof n.getDerivedStateFromError != "function" ? null : a.render(), t.flags |= 1, e !== null && r ? (t.child = oo(t, e.child, null, i), t.child = oo(t, null, n, i)) : jc(e, t, n, i), t.memoizedState = a.state, e = t.child) : e = ol(e, t, i), e;
	}
	function Gc(e, t, n, r) {
		return sa(), t.flags |= 256, jc(e, t, n, r), t.child;
	}
	var Kc = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0,
		hydrationErrors: null
	};
	function qc(e) {
		return {
			baseLanes: e,
			cachePool: Ua()
		};
	}
	function Jc(e, t, n) {
		return e = e === null ? 0 : e.childLanes & ~n, t && (e |= ld), e;
	}
	function Yc(e, t, n) {
		var r = t.pendingProps, i = !1, a = !!(t.flags & 128), o;
		if ((o = a) || (o = e !== null && e.memoizedState === null ? !1 : !!(No.current & 2)), o && (i = !0, t.flags &= -129), o = !!(t.flags & 32), t.flags &= -33, e === null) {
			if (W) {
				if (i ? Oo(t) : jo(), (e = $i) ? (e = am(e, ta), e = e !== null && e.data !== "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Wi === null ? null : {
						id: Gi,
						overflow: Ki
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = Pi(e), n.return = t, t.child = n, Qi = t, $i = null)) : e = null, e === null) throw ra(t);
				return t.lanes = sm(e) ? 32 : 536870912, null;
			}
			return a = r.children, r = r.fallback, i ? (jo(), i = t.mode, a = Zc({
				mode: "hidden",
				children: a
			}, i), r = Mi(r, i, n, null), a.return = t, r.return = t, a.sibling = r, t.child = a, r = t.child, r.memoizedState = qc(n), r.childLanes = Jc(e, o, n), t.memoizedState = Kc, Ic(null, r)) : (Oo(t), Xc(t, a));
		}
		var s = e.memoizedState;
		if (s !== null) {
			var c = s.dehydrated;
			if (c !== null) return $c(e, t, a, o, r, c, s, n);
		}
		return i ? (jo(), i = r.fallback, a = t.mode, s = e.child, c = s.sibling, r = ki(s, {
			mode: "hidden",
			children: r.children
		}), r.subtreeFlags = s.subtreeFlags & 1206910976, c === null ? (i = Mi(i, a, n, null), i.flags |= 2) : i = ki(c, i), i.return = t, r.return = t, r.sibling = i, t.child = r, Ic(null, r), r = t.child, i = e.child.memoizedState, i === null ? i = qc(n) : (a = i.cachePool, a === null ? a = Ua() : (s = Ea._currentValue, a = a.parent === s ? a : {
			parent: s,
			pool: s
		}), i = {
			baseLanes: i.baseLanes | n,
			cachePool: a
		}), r.memoizedState = i, r.childLanes = Jc(e, o, n), t.memoizedState = Kc, Ic(e.child, r)) : (Oo(t), n = e.child, e = n.sibling, n = ki(n, {
			mode: "visible",
			children: r.children
		}), n.return = t, n.sibling = null, e !== null && (o = t.deletions, o === null ? (t.deletions = [e], t.flags |= 16) : o.push(e)), t.child = n, t.memoizedState = null, n);
	}
	function Xc(e, t) {
		return t = Zc({
			mode: "visible",
			children: t
		}, e.mode), t.return = e, e.child = t;
	}
	function Zc(e, t) {
		return e = Di(22, e, null, t), e.lanes = 0, e;
	}
	function Qc(e, t, n) {
		return oo(t, e.child, null, n), e = Xc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function $c(e, t, n, r, a, o, s, c) {
		if (n) return t.flags & 256 ? (Oo(t), t.flags &= -257, Qc(e, t, c)) : t.memoizedState === null ? (jo(), o = a.fallback, s = t.mode, a = Zc({
			mode: "visible",
			children: a.children
		}, s), o = Mi(o, s, c, null), o.flags |= 2, a.return = t, o.return = t, a.sibling = o, t.child = a, oo(t, e.child, null, c), a = t.child, a.memoizedState = qc(c), a.childLanes = Jc(e, r, c), t.memoizedState = Kc, Ic(null, a)) : (jo(), t.child = e.child, t.flags |= 128, null);
		if (Oo(t), sm(o)) {
			if (r = o.nextSibling && o.nextSibling.dataset, r) var l = r.dgst;
			return r = l, r !== "" && (a = Error(i(419)), a.stack = "", a.digest = r, la({
				value: a,
				source: null,
				stack: null
			})), Qc(e, t, c);
		}
		if (Ac || _a(e, t, c, !1), r = (c & e.childLanes) !== 0, Ac || r) {
			if (xo.current !== null) return Qc(e, t, c);
			if (r = ed, r !== null && (a = ht(r, c), a !== 0 && a !== s.retryLane)) throw s.retryLane = a, Si(e, a), Md(r, e, a), kc;
			return om(o) || Wd(), Qc(e, t, c);
		}
		return om(o) ? (t.flags |= 192, t.child = e.child, null) : (e = s.treeContext, $i = lm(o.nextSibling), Qi = t, W = !0, ea = null, ta = !1, e !== null && Zi(t, e), t = Xc(t, a.children), t.flags |= 134221824, t);
	}
	function el(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), ha(e.return, t, n);
	}
	function tl(e) {
		for (var t = null; e !== null;) {
			var n = e.alternate;
			n !== null && Io(n) === null && (t = e), e = e.sibling;
		}
		return t;
	}
	function nl(e, t, n, r, i, a) {
		var o = e.memoizedState;
		o === null ? e.memoizedState = {
			isBackwards: t,
			rendering: null,
			renderingStartTime: 0,
			last: r,
			tail: n,
			tailMode: i,
			treeForkCount: a
		} : (o.isBackwards = t, o.rendering = null, o.renderingStartTime = 0, o.last = r, o.tail = n, o.tailMode = i, o.treeForkCount = a);
	}
	function rl(e) {
		var t = e.child;
		for (e.child = null; t !== null;) {
			var n = t.sibling;
			t.sibling = e.child, e.child = t, t = n;
		}
	}
	function il(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		r = r.children;
		var o = No.current;
		if (t.flags & 128) return Po(t, o), null;
		var s = !!(o & 2);
		if (s ? (o = o & 1 | 2, t.flags |= 128) : o &= 1, Po(t, o), i === "backwards" && e !== null ? (rl(e), jc(e, t, r, n), rl(e)) : jc(e, t, r, n), r = W ? Vi : 0, !s && e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
			if (e.tag === 13) e.memoizedState !== null && el(e, n, t);
			else if (e.tag === 19) el(e, n, t);
			else if (e.child !== null) {
				e.child.return = e, e = e.child;
				continue;
			}
			if (e === t) break a;
			for (; e.sibling === null;) {
				if (e.return === null || e.return === t) break a;
				e = e.return;
			}
			e.sibling.return = e.return, e = e.sibling;
		}
		switch (i) {
			case "backwards":
				n = tl(t.child), n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null, rl(t)), nl(t, !0, i, null, a, r);
				break;
			case "unstable_legacy-backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && Io(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				nl(t, !0, n, null, a, r);
				break;
			case "together":
				nl(t, !1, null, null, void 0, r);
				break;
			case "independent":
				t.memoizedState = null;
				break;
			default: n = tl(t.child), n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), nl(t, !1, i, n, a, r);
		}
		return t.child;
	}
	function al(e, t, n) {
		var r = t.pendingProps;
		return pa(t, t.type, r.value), jc(e, t, r.children, n), t.child;
	}
	function ol(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), od |= t.lanes, (n & t.childLanes) === 0) {
			if (e !== null) {
				if (_a(e, t, n, !1), (n & t.childLanes) === 0) return null;
			} else return null;
		}
		if (e !== null && t.child !== e.child) throw Error(i(153));
		if (t.child !== null) {
			for (e = t.child, n = ki(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = ki(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function sl(e, t) {
		return (e.lanes & t) !== 0 || (e = e.dependencies, !!(e !== null && va(e)));
	}
	function cl(e, t, n) {
		switch (t.tag) {
			case 3:
				Ce(t, t.stateNode.containerInfo), pa(t, Ea, e.memoizedState.cache), sa();
				break;
			case 27:
			case 5:
				Te(t);
				break;
			case 4:
				Ce(t, t.stateNode.containerInfo);
				break;
			case 10:
				pa(t, t.type, t.memoizedProps.value);
				break;
			case 31:
				if (t.memoizedState !== null) return t.flags |= 128, ko(t), null;
				break;
			case 13:
				var r = t.memoizedState;
				if (r !== null) {
					if (r.dehydrated !== null) return Oo(t), t.flags |= 128, null;
					r = _a(e, t, n, !1);
					var i = t.child.childLanes;
					return r || (n & i) !== 0 ? Yc(e, t, n) : (Oo(t), e = ol(e, t, n), e === null ? null : e.sibling);
				}
				Oo(t);
				break;
			case 19:
				if (t.flags & 128) return il(e, t, n);
				if (i = !!(e.flags & 128), r = (n & t.childLanes) !== 0, r ||= (_a(e, t, n, !1), (n & t.childLanes) !== 0), i) {
					if (r) return il(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), Po(t, No.current), r) break;
				return null;
			case 22: return t.lanes = 0, Fc(e, t, n, t.pendingProps);
			case 24: pa(t, Ea, e.memoizedState.cache);
		}
		return ol(e, t, n);
	}
	function ll(e, t, n) {
		if (e !== null) {
			if (e.memoizedProps !== t.pendingProps) Ac = !0;
			else {
				if (!sl(e, n) && !(t.flags & 128)) return Ac = !1, cl(e, t, n);
				Ac = !!(e.flags & 131072);
			}
		} else Ac = !1, W && t.flags & 1048576 && Ji(t, Vi, t.index);
		switch (t.lanes = 0, t.tag) {
			case 16:
				a: {
					var r = t.pendingProps;
					if (e = Xa(t.elementType), t.type = e, typeof e == "function") Oi(e) ? (r = yc(e, r), t.tag = 1, t = Wc(null, t, e, r, n)) : (t.tag = 0, t = Hc(null, t, e, r, n));
					else {
						if (e != null) {
							var a = e.$$typeof;
							if (a === ee) {
								t.tag = 11, t = Mc(null, t, e, r, n);
								break a;
							}
							if (a === ne) {
								t.tag = 14, t = Nc(null, t, e, r, n);
								break a;
							}
							if (a === N) {
								t.tag = 10, t.type = e, t = al(null, t, n);
								break a;
							}
						}
						throw t = de(e) || e, Error(i(306, t, ""));
					}
				}
				return t;
			case 0: return Hc(e, t, t.type, t.pendingProps, n);
			case 1: return r = t.type, a = yc(r, t.pendingProps), Wc(e, t, r, a, n);
			case 3:
				a: {
					if (Ce(t, t.stateNode.containerInfo), e === null) throw Error(i(387));
					r = t.pendingProps;
					var o = t.memoizedState;
					a = o.element, uo(e, t), vo(t, r, null, n);
					var s = t.memoizedState;
					if (r = s.cache, pa(t, Ea, r), r !== o.cache && ga(t, [Ea], n, !0), _o(), r = s.element, o.isDehydrated) {
						if (o = {
							element: r,
							isDehydrated: !1,
							cache: s.cache
						}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
							t = Gc(e, t, r, n);
							break a;
						}
						if (r !== a) {
							a = Li(Error(i(424)), t), la(a), t = Gc(e, t, r, n);
							break a;
						}
						switch (e = t.stateNode.containerInfo, e.nodeType) {
							case 9:
								e = e.body;
								break;
							default: e = e.nodeName === "HTML" ? e.ownerDocument.body : e;
						}
						for ($i = lm(e.firstChild), Qi = t, W = !0, ea = null, ta = !0, n = so(t, null, r, n), t.child = n; n;) n.flags = n.flags & -3 | 134221824, n = n.sibling;
					} else {
						if (sa(), r === a) {
							t = ol(e, t, n);
							break a;
						}
						jc(e, t, r, n);
					}
					t = t.child;
				}
				return t;
			case 26: return Vc(e, t), e === null ? (n = Nm(t.type, null, t.pendingProps, null)) ? t.memoizedState = n : W || (t.stateNode = fp(t.type, t.pendingProps, xe.current, t)) : t.memoizedState = Nm(t.type, e.memoizedProps, t.pendingProps, e.memoizedState), null;
			case 27: return Te(t), e === null && W && (r = t.stateNode = hm(t.type, t.pendingProps, xe.current), Qi = t, ta = !0, a = $i, Sp(t.type) ? (um = a, $i = lm(r.firstChild)) : $i = a), jc(e, t, t.pendingProps.children, n), Vc(e, t), e === null && (t.flags |= 4194304), t.child;
			case 5: return e === null && W && ((a = r = $i) && (r = rm(r, t.type, t.pendingProps, ta), r === null ? a = !1 : (t.stateNode = r, Qi = t, $i = lm(r.firstChild), ta = !1, a = !0)), a || ra(t)), Te(t), a = t.type, o = t.pendingProps, s = e === null ? null : e.memoizedProps, r = o.children, pp(a, o) ? r = null : s !== null && pp(a, s) && (t.flags |= 32), t.memoizedState !== null && (a = Yo(e, t, Qo, null, null, n), sh._currentValue = a), Vc(e, t), jc(e, t, r, n), t.child;
			case 6: return e === null && W && ((e = n = $i) && (n = im(n, t.pendingProps, ta), n === null ? e = !1 : (t.stateNode = n, Qi = t, $i = null, e = !0)), e || ra(t)), null;
			case 13: return Yc(e, t, n);
			case 4: return Ce(t, t.stateNode.containerInfo), r = t.pendingProps, e === null ? t.child = oo(t, null, r, n) : jc(e, t, r, n), t.child;
			case 11: return Mc(e, t, t.type, t.pendingProps, n);
			case 7: return r = t.pendingProps, Vc(e, t), jc(e, t, r, n), t.child;
			case 8: return jc(e, t, t.pendingProps.children, n), t.child;
			case 12: return jc(e, t, t.pendingProps.children, n), t.child;
			case 10: return al(e, t, n);
			case 9: return a = t.type._context, r = t.pendingProps.children, ya(t), a = ba(a), r = r(a), t.flags |= 1, jc(e, t, r, n), t.child;
			case 14: return Nc(e, t, t.type, t.pendingProps, n);
			case 15: return Pc(e, t, t.type, t.pendingProps, n);
			case 19: return il(e, t, n);
			case 31: return Bc(e, t, n);
			case 22: return Fc(e, t, n, t.pendingProps);
			case 24: return ya(t), r = ba(Ea), e === null ? (a = Va(), a === null && (a = ed, o = Da(), a.pooledCache = o, o.refCount++, o !== null && (a.pooledCacheLanes |= n), a = o), t.memoizedState = {
				parent: r,
				cache: a
			}, lo(t), pa(t, Ea, a)) : ((e.lanes & n) !== 0 && (uo(e, t), vo(t, null, null, n), _o()), a = e.memoizedState, o = t.memoizedState, a.parent === r ? (r = o.cache, pa(t, Ea, r), r !== a.cache && ga(t, [Ea], n, !0)) : (a = {
				parent: r,
				cache: r
			}, t.memoizedState = a, t.lanes === 0 && (t.memoizedState = t.updateQueue.baseState = a), pa(t, Ea, r))), jc(e, t, t.pendingProps.children, n), t.child;
			case 30: return t.stateNode === null && (t.stateNode = {
				autoName: null,
				paired: null,
				clones: null,
				ref: null
			}), r = t.pendingProps, r.name != null && r.name !== "auto" ? t.flags |= e === null ? 18882560 : 18874368 : W && Yi(t), e !== null && e.memoizedProps.name !== r.name ? t.flags |= 4194816 : Vc(e, t), jc(e, t, r.children, n), t.child;
			case 29: throw t.pendingProps;
		}
		throw Error(i(156, t.tag));
	}
	function ul(e) {
		e.flags |= 4;
	}
	function dl(e, t, n, r, i) {
		var a;
		if ((a = !!(e.mode & 32)) && (a = n === null ? Jm(t, r) : Jm(t, r) && (r.src !== n.src || r.srcSet !== n.srcSet)), a) {
			if (e.flags |= 16777216, (i & 335544128) === i) {
				if (e.stateNode.complete) e.flags |= 8192;
				else if (Vd()) e.flags |= 8192;
				else throw Za = qa, Ga;
			}
		} else e.flags &= -16777217;
	}
	function fl(e, t) {
		if (t.type !== "stylesheet" || t.state.loading & 4) e.flags &= -16777217;
		else if (e.flags |= 16777216, !Ym(t)) {
			if (Vd()) e.flags |= 8192;
			else throw Za = qa, Ga;
		}
	}
	function pl(e, t) {
		t !== null && (e.flags |= 4), e.flags & 16384 && (t = e.tag === 22 ? 536870912 : lt(), e.lanes |= t, ud |= t);
	}
	function ml(e, t) {
		if (!W) switch (e.tailMode) {
			case "visible": break;
			case "collapsed":
				for (var n = e.tail, r = null; n !== null;) n.alternate !== null && (r = n), n = n.sibling;
				r === null ? t || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
				break;
			default:
				for (t = e.tail, n = null; t !== null;) t.alternate !== null && (n = t), t = t.sibling;
				n === null ? e.tail = null : n.sibling = null;
		}
	}
	function K(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 1206910976, r |= i.flags & 1206910976, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function hl(e, t, n) {
		var r = t.pendingProps;
		switch (Xi(t), t.tag) {
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return K(t), null;
			case 1: return K(t), null;
			case 3: return n = t.stateNode, r = null, e !== null && (r = e.memoizedState.cache), t.memoizedState.cache !== r && (t.flags |= 2048), ma(Ea), we(), n.pendingContext && (n.context = n.pendingContext, n.pendingContext = null), (e === null || e.child === null) && (oa(t) ? ul(t) : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, ca())), K(t), null;
			case 26:
				var a = t.type, o = t.memoizedState;
				return e === null ? (ul(t), o === null ? (K(t), dl(t, a, null, r, n)) : (K(t), fl(t, o))) : o ? o === e.memoizedState ? (K(t), t.flags &= -16777217) : (ul(t), K(t), fl(t, o)) : (e = e.memoizedProps, e !== r && ul(t), K(t), dl(t, a, e, r, n)), null;
			case 27:
				if (Ee(t), n = xe.current, a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && ul(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return K(t), t.subtreeFlags &= -33554433, null;
					}
					e = ye.current, oa(t) ? ia(t, e) : (e = hm(a, r, n), t.stateNode = e, ul(t));
				}
				return K(t), t.subtreeFlags &= -33554433, null;
			case 5:
				if (Ee(t), a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && ul(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return K(t), t.subtreeFlags &= -33554433, null;
					}
					if (o = ye.current, oa(t)) ia(t, o);
					else {
						var s = lp(xe.current);
						switch (o) {
							case 1:
								o = s.createElementNS("http://www.w3.org/2000/svg", a);
								break;
							case 2:
								o = s.createElementNS("http://www.w3.org/1998/Math/MathML", a);
								break;
							default: switch (a) {
								case "svg":
									o = s.createElementNS("http://www.w3.org/2000/svg", a);
									break;
								case "math":
									o = s.createElementNS("http://www.w3.org/1998/Math/MathML", a);
									break;
								case "script":
									o = s.createElement("div"), o.innerHTML = "<script><\/script>", o = o.removeChild(o.firstChild);
									break;
								case "select":
									o = typeof r.is == "string" ? s.createElement("select", { is: r.is }) : s.createElement("select"), r.multiple ? o.multiple = !0 : r.size && (o.size = r.size);
									break;
								default: o = typeof r.is == "string" ? s.createElement(a, { is: r.is }) : s.createElement(a);
							}
						}
						o[xt] = t, o[R] = r;
						a: for (s = t.child; s !== null;) {
							if (s.tag === 5 || s.tag === 6) o.appendChild(s.stateNode);
							else if (s.tag !== 4 && s.tag !== 27 && s.child !== null) {
								s.child.return = s, s = s.child;
								continue;
							}
							if (s === t) break a;
							for (; s.sibling === null;) {
								if (s.return === null || s.return === t) break a;
								s = s.return;
							}
							s.sibling.return = s.return, s = s.sibling;
						}
						t.stateNode = o;
						a: switch (np(o, a, r), a) {
							case "button":
							case "input":
							case "select":
							case "textarea":
								r = !!r.autoFocus;
								break a;
							case "img":
								r = !0;
								break a;
							default: r = !1;
						}
						r && ul(t);
					}
				}
				return K(t), t.subtreeFlags &= -33554433, dl(t, t.type, e === null ? null : e.memoizedProps, t.pendingProps, n), null;
			case 6:
				if (e && t.stateNode != null) e.memoizedProps !== r && ul(t);
				else {
					if (typeof r != "string" && t.stateNode === null) throw Error(i(166));
					if (e = xe.current, oa(t)) {
						if (e = t.stateNode, n = t.memoizedProps, r = null, a = Qi, a !== null) switch (a.tag) {
							case 27:
							case 5: r = a.memoizedProps;
						}
						e[xt] = t, e = !!(e.nodeValue === n || r !== null && !0 === r.suppressHydrationWarning || $f(e.nodeValue, n)), e || ra(t, !0);
					} else e = lp(e).createTextNode(r), e[xt] = t, t.stateNode = e;
				}
				return K(t), null;
			case 31:
				if (n = t.memoizedState, e === null || e.memoizedState !== null) {
					if (r = oa(t), n !== null) {
						if (e === null) {
							if (!r) throw Error(i(318));
							if (e = t.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(557));
							e[xt] = t;
						} else sa(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						K(t), e = !1;
					} else n = ca(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = n), e = !0;
					if (!e) return t.flags & 256 ? (Mo(t), t) : (Mo(t), null);
					if (t.flags & 128) throw Error(i(558));
				}
				return K(t), null;
			case 13:
				if (r = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (a = oa(t), r !== null && r.dehydrated !== null) {
						if (e === null) {
							if (!a) throw Error(i(318));
							if (a = t.memoizedState, a = a === null ? null : a.dehydrated, !a) throw Error(i(317));
							a[xt] = t;
						} else sa(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						K(t), a = !1;
					} else a = ca(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = a), a = !0;
					if (!a) return t.flags & 256 ? (Mo(t), t) : (Mo(t), null);
				}
				return Mo(t), t.flags & 128 ? (t.lanes = n, t) : (n = r !== null, e = e !== null && e.memoizedState !== null, n && (r = t.child, a = null, r.alternate !== null && r.alternate.memoizedState !== null && r.alternate.memoizedState.cachePool !== null && (a = r.alternate.memoizedState.cachePool.pool), o = null, r.memoizedState !== null && r.memoizedState.cachePool !== null && (o = r.memoizedState.cachePool.pool), o !== a && (r.flags |= 2048)), n !== e && n && (t.child.flags |= 8192), pl(t, t.updateQueue), K(t), null);
			case 4: return we(), e === null && Uf(t.stateNode.containerInfo), t.flags |= 67108864, K(t), null;
			case 10: return ma(t.type), K(t), null;
			case 19:
				if (Fo(t), r = t.memoizedState, r === null) return K(t), null;
				if (a = !!(t.flags & 128), o = r.rendering, o === null) {
					if (a) ml(r, !1);
					else {
						if (ad !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
							if (o = Io(e), o !== null) {
								for (t.flags |= 128, ml(r, !1), e = o.updateQueue, t.updateQueue = e, pl(t, e), t.subtreeFlags = 0, e = n, n = t.child; n !== null;) Ai(n, e), n = n.sibling;
								return Po(t, No.current & 1 | 2), W && qi(t, r.treeForkCount), t.child;
							}
							e = e.sibling;
						}
						r.tail !== null && ze() > hd && (t.flags |= 128, a = !0, ml(r, !1), t.lanes = 4194304);
					}
				} else {
					if (!a) {
						if (e = Io(o), e !== null) {
							if (t.flags |= 128, a = !0, e = e.updateQueue, t.updateQueue = e, pl(t, e), ml(r, !0), r.tail === null && r.tailMode !== "collapsed" && r.tailMode !== "visible" && !o.alternate && !W) return K(t), null;
						} else 2 * ze() - r.renderingStartTime > hd && n !== 536870912 && (t.flags |= 128, a = !0, ml(r, !1), t.lanes = 4194304);
					}
					r.isBackwards ? (o.sibling = t.child, t.child = o) : (e = r.last, e === null ? t.child = o : e.sibling = o, r.last = o);
				}
				if (r.tail !== null) {
					e = r.tail;
					a: {
						for (n = e; n !== null;) {
							if (n.alternate !== null) {
								n = !1;
								break a;
							}
							n = n.sibling;
						}
						n = !0;
					}
					return r.rendering = e, r.tail = e.sibling, r.renderingStartTime = ze(), e.sibling = null, o = No.current, o = a ? o & 1 | 2 : o & 1, r.tailMode === "visible" || r.tailMode === "collapsed" || !n || W ? Po(t, o) : (n = o, ve(Eo, t), ve(No, n), Do === null && (Do = t)), W && qi(t, r.treeForkCount), e;
				}
				return K(t), null;
			case 22:
			case 23: return Mo(t), To(), r = t.memoizedState !== null, e === null ? r && (t.flags |= 8192) : e.memoizedState !== null !== r && (t.flags |= 8192), r ? n & 536870912 && !(t.flags & 128) && (K(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : K(t), n = t.updateQueue, n !== null && pl(t, n.retryQueue), n = null, e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), r = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (r = t.memoizedState.cachePool.pool), r !== n && (t.flags |= 2048), e !== null && _e(Ba), null;
			case 24: return n = null, e !== null && (n = e.memoizedState.cache), t.memoizedState.cache !== n && (t.flags |= 2048), ma(Ea), K(t), null;
			case 25: return null;
			case 30: return t.flags |= 33554432, K(t), null;
		}
		throw Error(i(156, t.tag));
	}
	function gl(e, t) {
		switch (Xi(t), t.tag) {
			case 1: return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return ma(Ea), we(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 26:
			case 27:
			case 5: return Ee(t), null;
			case 31:
				if (t.memoizedState !== null) {
					if (Mo(t), t.alternate === null) throw Error(i(340));
					sa();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 13:
				if (Mo(t), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(i(340));
					sa();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return Fo(t), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, e = t.memoizedState, e !== null && (e.rendering = null, e.tail = null), t.flags |= 4, t) : null;
			case 4: return we(), null;
			case 10: return ma(t.type), null;
			case 22:
			case 23: return Mo(t), To(), e !== null && _e(Ba), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 24: return ma(Ea), null;
			case 25: return null;
			default: return null;
		}
	}
	function _l(e, t) {
		switch (Xi(t), t.tag) {
			case 3:
				ma(Ea), we();
				break;
			case 26:
			case 27:
			case 5:
				Ee(t);
				break;
			case 4:
				we();
				break;
			case 31:
				t.memoizedState !== null && Mo(t);
				break;
			case 13:
				Mo(t);
				break;
			case 19:
				Fo(t);
				break;
			case 10:
				ma(t.type);
				break;
			case 22:
			case 23:
				Mo(t), To(), e !== null && _e(Ba);
				break;
			case 24: ma(Ea);
		}
	}
	function vl(e, t) {
		try {
			var n = t.updateQueue, r = n === null ? null : n.lastEffect;
			if (r !== null) {
				var i = r.next;
				n = i;
				do {
					if ((n.tag & e) === e) {
						r = void 0;
						var a = n.create, o = n.inst;
						r = a(), o.destroy = r;
					}
					n = n.next;
				} while (n !== i);
			}
		} catch (e) {
			ff(t, t.return, e);
		}
	}
	function yl(e, t, n) {
		try {
			var r = t.updateQueue, i = r === null ? null : r.lastEffect;
			if (i !== null) {
				var a = i.next;
				r = a;
				do {
					if ((r.tag & e) === e) {
						var o = r.inst, s = o.destroy;
						if (s !== void 0) {
							o.destroy = void 0, i = t;
							var c = n, l = s;
							try {
								l();
							} catch (e) {
								ff(i, c, e);
							}
						}
					}
					r = r.next;
				} while (r !== a);
			}
		} catch (e) {
			ff(t, t.return, e);
		}
	}
	function bl(e) {
		var t = e.updateQueue;
		if (t !== null) {
			var n = e.stateNode;
			try {
				bo(t, n);
			} catch (t) {
				ff(e, e.return, t);
			}
		}
	}
	function xl(e, t, n) {
		n.props = yc(e.type, e.memoizedProps), n.state = e.memoizedState;
		try {
			n.componentWillUnmount();
		} catch (n) {
			ff(e, t, n);
		}
	}
	function Sl(e, t) {
		try {
			var n = e.ref;
			if (n !== null) {
				switch (e.tag) {
					case 26:
					case 27:
					case 5:
						var r = e.stateNode;
						break;
					case 30:
						var i = e.stateNode, a = fi(e.memoizedProps, i);
						(i.ref === null || i.ref.name !== a) && (i.ref = Pp(a)), r = i.ref;
						break;
					case 7:
						if (e.stateNode === null) {
							var o = new Fp(e);
							f(e.child, !1, Qp, o, void 0, void 0), e.stateNode = o;
						}
						r = e.stateNode;
						break;
					default: r = e.stateNode;
				}
				typeof n == "function" ? e.refCleanup = n(r) : n.current = r;
			}
		} catch (n) {
			ff(e, t, n);
		}
	}
	function Cl(e, t) {
		var n = e.ref, r = e.refCleanup;
		if (n !== null) {
			if (typeof r == "function") try {
				r();
			} catch (n) {
				ff(e, t, n);
			} finally {
				e.refCleanup = null, e = e.alternate, e != null && (e.refCleanup = null);
			}
			else if (typeof n == "function") try {
				n(null);
			} catch (n) {
				ff(e, t, n);
			}
			else n.current = null;
		}
	}
	function wl(e, t) {
		if ((e.tag === 5 || e.tag === 27 || e.tag === 6) && e.alternate === null && t !== null) for (var n = 0; n < t.length; n++) em(e.stateNode, t[n]);
	}
	function Tl(e) {
		for (var t = e.return; t !== null && (Ol(t) && em(e.stateNode, t.stateNode), !Dl(t));) t = t.return;
	}
	function El(e) {
		for (var t = e.return; t !== null && (Ol(t) && tm(e.stateNode, t.stateNode), !Dl(t));) t = t.return;
	}
	function Dl(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 27;
	}
	function Ol(e) {
		return e && e.tag === 7 && e.stateNode !== null;
	}
	function kl(e) {
		var t = e.type, n = e.memoizedProps, r = e.stateNode;
		try {
			a: switch (t) {
				case "button":
				case "input":
				case "select":
				case "textarea":
					n.autoFocus && r.focus();
					break a;
				case "img": n.src ? r.src = n.src : n.srcSet && (r.srcset = n.srcSet);
			}
		} catch (t) {
			ff(e, e.return, t);
		}
	}
	function Al(e, t, n) {
		try {
			var r = e.stateNode;
			ip(r, e.type, n, t), r[R] = t;
		} catch (t) {
			ff(e, e.return, t);
		}
	}
	function jl(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 26 || e.tag === 27 && Sp(e.type) || e.tag === 4;
	}
	function Ml(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || jl(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.tag === 27 && Sp(e.type) || e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function Nl(e, t, n, r) {
		var i = e.tag;
		if (i === 5 || i === 6) i = e.stateNode, t ? (n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n).insertBefore(i, t) : (t = n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n, t.appendChild(i), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = pn)), wl(e, r), V = !0;
		else if (i !== 4 && (i === 27 && (wl(e, r), r = null, Sp(e.type) && (n = e.stateNode, t = null)), e = e.child, e !== null)) for (Nl(e, t, n, r), e = e.sibling; e !== null;) Nl(e, t, n, r), e = e.sibling;
	}
	function Pl(e, t, n, r) {
		var i = e.tag;
		if (i === 5 || i === 6) i = e.stateNode, t ? n.insertBefore(i, t) : n.appendChild(i), wl(e, r), V = !0;
		else if (i !== 4 && (i === 27 && (wl(e, r), r = null, Sp(e.type) && (n = e.stateNode)), e = e.child, e !== null)) for (Pl(e, t, n, r), e = e.sibling; e !== null;) Pl(e, t, n, r), e = e.sibling;
	}
	function Fl(e) {
		var t = e.stateNode, n = e.memoizedProps;
		try {
			for (var r = e.type, i = t.attributes; i.length;) t.removeAttributeNode(i[0]);
			np(t, r, n), t[xt] = e, t[R] = n;
		} catch (t) {
			ff(e, e.return, t);
		}
	}
	var Il = !1, Ll = null;
	function Rl(e) {
		(e.tag === 30 || e.subtreeFlags & 33554432) && (Il = !0);
	}
	var zl = null;
	function Bl() {
		var e = zl;
		return zl = null, e;
	}
	var Vl = 0;
	function Hl(e, t, n, r, i) {
		return Vl = 0, Ul(e.child, t, n, r, i);
	}
	function Ul(e, t, n, r, i) {
		for (var a = !1; e !== null;) {
			if (e.tag === 5) {
				var o = e.stateNode;
				if (r !== null) {
					var s = Op(o);
					r.push(s), s.view && (a = !0);
				} else a || Op(o).view && (a = !0);
				Il = !0, Tp(o, Vl === 0 ? t : t + "_" + Vl, n), Vl++;
			} else (e.tag !== 22 || e.memoizedState === null) && (e.tag === 30 && i || Ul(e.child, t, n, r, i) && (a = !0));
			e = e.sibling;
		}
		return a;
	}
	function Wl(e, t) {
		for (; e !== null;) e.tag === 5 ? Ep(e.stateNode, e.memoizedProps) : (e.tag !== 22 || e.memoizedState === null) && (e.tag === 30 && t || Wl(e.child, t)), e = e.sibling;
	}
	function Gl(e) {
		if (e.subtreeFlags & 18874368) for (e = e.child; e !== null;) {
			if ((e.tag !== 22 || e.memoizedState === null) && (Gl(e), e.tag === 30 && e.flags & 18874368 && e.stateNode.paired)) {
				var t = e.memoizedProps;
				if (t.name == null || t.name === "auto") throw Error(i(544));
				var n = t.name;
				t = mi(t.default, t.share), t !== "none" && (Hl(e, n, t, null, !1) || Wl(e.child, !1));
			}
			e = e.sibling;
		}
	}
	function Kl(e, t) {
		if (e.tag === 30) {
			var n = e.stateNode, r = e.memoizedProps, i = fi(r, n), a = mi(r.default, n.paired ? r.share : r.enter);
			a === "none" ? Gl(e) : Hl(e, i, a, null, !1) ? (Gl(e), n.paired || t || jd(e, r.onEnter)) : Wl(e.child, !1);
		} else if (e.subtreeFlags & 33554432) for (e = e.child; e !== null;) Kl(e, t), e = e.sibling;
		else Gl(e);
	}
	function ql(e) {
		if (Ll !== null && Ll.size !== 0) {
			var t = Ll;
			if (e.subtreeFlags & 18874368) for (e = e.child; e !== null;) {
				if (e.tag !== 22 || e.memoizedState === null) {
					if (e.tag === 30 && e.flags & 18874368) {
						var n = e.memoizedProps, r = n.name;
						if (r != null && r !== "auto") {
							var i = t.get(r);
							if (i !== void 0) {
								var a = mi(n.default, n.share);
								if (a !== "none" && (Hl(e, r, a, null, !1) ? (a = e.stateNode, i.paired = a, a.paired = i, jd(e, n.onShare)) : Wl(e.child, !1)), t.delete(r), t.size === 0) break;
							}
						}
					}
					ql(e);
				}
				e = e.sibling;
			}
		}
	}
	function Jl(e) {
		if (e.tag === 30) {
			var t = e.memoizedProps, n = fi(t, e.stateNode), r = Ll === null ? void 0 : Ll.get(n), i = mi(t.default, r === void 0 ? t.exit : t.share);
			i !== "none" && (Hl(e, n, i, null, !1) ? r === void 0 ? jd(e, t.onExit) : (i = e.stateNode, r.paired = i, i.paired = r, Ll.delete(n), jd(e, t.onShare)) : Wl(e.child, !1)), Ll !== null && ql(e);
		} else if (e.subtreeFlags & 33554432) for (e = e.child; e !== null;) Jl(e), e = e.sibling;
		else Ll !== null && ql(e);
	}
	function Yl(e) {
		for (e = e.child; e !== null;) {
			if (e.tag === 30) {
				var t = e.memoizedProps, n = fi(t, e.stateNode);
				t = mi(t.default, t.update), e.flags &= -5, t !== "none" && Hl(e, n, t, e.memoizedState = [], !1);
			} else e.subtreeFlags & 33554432 && Yl(e);
			e = e.sibling;
		}
	}
	function Xl(e) {
		if (e.subtreeFlags & 18874368) for (e = e.child; e !== null;) {
			if (e.tag !== 22 || e.memoizedState === null) {
				if (e.tag === 30 && e.flags & 18874368) {
					var t = e.stateNode;
					t.paired !== null && (t.paired = null, Wl(e.child, !1));
				}
				Xl(e);
			}
			e = e.sibling;
		}
	}
	function Zl(e) {
		if (e.tag === 30) e.stateNode.paired = null, Wl(e.child, !1), Xl(e);
		else if (e.subtreeFlags & 33554432) for (e = e.child; e !== null;) Zl(e), e = e.sibling;
		else Xl(e);
	}
	function Ql(e) {
		for (e = e.child; e !== null;) e.tag === 30 ? Wl(e.child, !1) : e.subtreeFlags & 33554432 && Ql(e), e = e.sibling;
	}
	function $l(e, t, n, r, i, a, o) {
		for (var s = !1; t !== null;) {
			if (t.tag === 5) {
				var c = t.stateNode;
				if (a !== null && Vl < a.length) {
					var l = a[Vl], u = Op(c);
					(l.view || u.view) && (s = !0);
					var d;
					if (d = !(e.flags & 4)) {
						if (u.clip) d = !0;
						else {
							d = l.rect;
							var f = u.rect;
							d = d.y !== f.y || d.x !== f.x || d.height !== f.height || d.width !== f.width;
						}
					}
					d && (e.flags |= 4), u.abs ? u = !l.abs : (l = l.rect, u = u.rect, u = l.height !== u.height || l.width !== u.width), u && (e.flags |= 32);
				} else e.flags |= 32;
				e.flags & 4 && Tp(c, Vl === 0 ? n : n + "_" + Vl, i), s && e.flags & 4 || (zl === null && (zl = []), zl.push(c, Vl === 0 ? r : r + "_" + Vl, t.memoizedProps)), Vl++;
			} else (t.tag !== 22 || t.memoizedState === null) && (t.tag === 30 && o ? e.flags |= t.flags & 32 : $l(e, t.child, n, r, i, a, o) && (s = !0));
			t = t.sibling;
		}
		return s;
	}
	function eu(e, t) {
		for (e = e.child; e !== null;) {
			if (e.tag === 30) {
				var n = e.memoizedProps, r = e.stateNode, i = fi(n, r), a = mi(n.default, n.update);
				if (t) {
					r = r.clones;
					var o = r === null ? null : r.map(kp);
				} else o = e.memoizedState, e.memoizedState = null;
				r = e;
				var s = e.child;
				Vl = 0, i = $l(r, s, i, i, a, o, !1), e.flags & 4 && i && (t || jd(e, n.onUpdate));
			} else e.subtreeFlags & 33554432 && eu(e, t);
			e = e.sibling;
		}
	}
	var tu = !1, nu = !1, ru = !1, iu = !1, au = typeof WeakSet == "function" ? WeakSet : Set, su = null, cu = !1, lu = !1, uu = !1, du = !1;
	function fu(e, t, n) {
		if (e = e.containerInfo, sp = gh, e = Hr(e), Ur(e)) {
			if ("selectionStart" in e) var r = {
				start: e.selectionStart,
				end: e.selectionEnd
			};
			else a: {
				r = (r = e.ownerDocument) && r.defaultView || window;
				var i = r.getSelection && r.getSelection();
				if (i && i.rangeCount !== 0) {
					r = i.anchorNode;
					var a = i.anchorOffset, o = i.focusNode;
					i = i.focusOffset;
					try {
						r.nodeType, o.nodeType;
					} catch {
						r = null;
						break a;
					}
					var s = 0, c = -1, l = -1, u = 0, d = 0, f = e, p = null;
					b: for (;;) {
						for (var m; f !== r || a !== 0 && f.nodeType !== 3 || (c = s + a), f !== o || i !== 0 && f.nodeType !== 3 || (l = s + i), f.nodeType === 3 && (s += f.nodeValue.length), (m = f.firstChild) !== null;) p = f, f = m;
						for (;;) {
							if (f === e) break b;
							if (p === r && ++u === a && (c = s), p === o && ++d === i && (l = s), (m = f.nextSibling) !== null) break;
							f = p, p = f.parentNode;
						}
						f = m;
					}
					r = c === -1 || l === -1 ? null : {
						start: c,
						end: l
					};
				} else r = null;
			}
			r ||= {
				start: 0,
				end: 0
			};
		} else r = null;
		for (cp = {
			focusedElem: e,
			selectionRange: r
		}, gh = !1, n = (n & 335544064) === n, su = t, t = n ? 9270 : 1024; su !== null;) {
			if (e = su, n && (r = e.deletions, r !== null)) for (a = 0; a < r.length; a++) n && Jl(r[a]);
			if (e.alternate === null && e.flags & 2) n && Rl(e), pu(n);
			else {
				if (e.tag === 22) {
					if (r = e.alternate, e.memoizedState !== null) {
						r !== null && r.memoizedState === null && n && Jl(r), pu(n);
						continue;
					}
					if (r !== null && r.memoizedState !== null) {
						n && Rl(e), pu(n);
						continue;
					}
				}
				r = e.child, (e.subtreeFlags & t) !== 0 && r !== null ? (r.return = e, su = r) : (n && Yl(e), pu(n));
			}
		}
		Ll = null;
	}
	function pu(e) {
		for (; su !== null;) {
			var t = su, n = e, r = t.alternate, a = t.flags;
			switch (t.tag) {
				case 0:
				case 11:
				case 15: break;
				case 1:
					if (a & 1024 && r !== null) {
						n = void 0, a = r.memoizedProps, r = r.memoizedState;
						var o = t.stateNode;
						try {
							var s = yc(t.type, a);
							n = o.getSnapshotBeforeUpdate(s, r), o.__reactInternalSnapshotBeforeUpdate = n;
						} catch (e) {
							ff(t, t.return, e);
						}
					}
					break;
				case 3:
					if (a & 1024) {
						if (r = t.stateNode.containerInfo, n = r.nodeType, n === 9) nm(r);
						else if (n === 1) switch (r.nodeName) {
							case "HEAD":
							case "HTML":
							case "BODY":
								nm(r);
								break;
							default: r.textContent = "";
						}
					}
					break;
				case 5:
				case 26:
				case 27:
				case 6:
				case 4:
				case 17: break;
				case 30:
					n && r !== null && (n = fi(r.memoizedProps, r.stateNode), a = t.memoizedProps, a = mi(a.default, a.update), a !== "none" && Hl(r, n, a, r.memoizedState = [], !0));
					break;
				default: if (a & 1024) throw Error(i(163));
			}
			if (r = t.sibling, r !== null) {
				r.return = t.return, su = r;
				break;
			}
			su = t.return;
		}
	}
	function mu(e, t, n) {
		var r = n.flags;
		switch (n.tag) {
			case 0:
			case 11:
			case 15:
				Pu(e, n), r & 4 && vl(5, n);
				break;
			case 1:
				if (Pu(e, n), r & 4) {
					if (e = n.stateNode, t === null) try {
						e.componentDidMount();
					} catch (e) {
						ff(n, n.return, e);
					}
					else {
						var i = yc(n.type, t.memoizedProps);
						t = t.memoizedState;
						try {
							e.componentDidUpdate(i, t, e.__reactInternalSnapshotBeforeUpdate);
						} catch (e) {
							ff(n, n.return, e);
						}
					}
				}
				r & 64 && bl(n), r & 512 && Sl(n, n.return);
				break;
			case 3:
				if (Pu(e, n), r & 64 && (e = n.updateQueue, e !== null)) {
					if (t = null, n.child !== null) switch (n.child.tag) {
						case 27:
						case 5:
							t = n.child.stateNode;
							break;
						case 1: t = n.child.stateNode;
					}
					try {
						bo(e, t);
					} catch (e) {
						ff(n, n.return, e);
					}
				}
				break;
			case 27: t === null && r & 4 && Fl(n);
			case 26:
			case 5:
				Pu(e, n), t === null && r & 4 && kl(n), r & 512 && Sl(n, n.return);
				break;
			case 12:
				Pu(e, n);
				break;
			case 31:
				Pu(e, n), r & 4 && Cu(e, n);
				break;
			case 13:
				Pu(e, n), r & 4 && wu(e, n), r & 64 && (e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null && (n = gf.bind(null, n), cm(e, n))));
				break;
			case 22:
				if (r = n.memoizedState !== null || tu, !r) {
					var a = t !== null && t.memoizedState !== null || nu;
					t = tu, i = nu, tu = r, (nu = a) && !i ? (r = 2, n.subtreeFlags & 8772 && (r |= 1), Iu(e, n, r)) : Pu(e, n), tu = t, nu = i;
				}
				break;
			case 30:
				Pu(e, n), r & 512 && Sl(n, n.return);
				break;
			case 7: r & 512 && Sl(n, n.return);
			default: Pu(e, n);
		}
	}
	function hu(e, t) {
		for (e = e.child; e !== null;) gu(e, t), e = e.sibling;
	}
	function gu(e, t) {
		switch (e.tag) {
			case 5:
			case 26:
				try {
					var n = e.stateNode;
					if (t) {
						var r = n.style;
						typeof r.setProperty == "function" ? r.setProperty("display", "none", "important") : r.display = "none";
					} else {
						var i = e.stateNode, a = e.memoizedProps.style, o = a != null && a.hasOwnProperty("display") ? a.display : null;
						i.style.display = o == null || typeof o == "boolean" ? "" : ("" + o).trim();
					}
				} catch (t) {
					ff(e, e.return, t);
				}
				_u(e, t);
				break;
			case 6:
				try {
					e.stateNode.nodeValue = t ? "" : e.memoizedProps, V = !0;
				} catch (t) {
					ff(e, e.return, t);
				}
				break;
			case 18:
				try {
					var s = e.stateNode;
					t ? wp(s, !0) : wp(e.stateNode, !1);
				} catch (t) {
					ff(e, e.return, t);
				}
				break;
			case 22:
			case 23:
				e.memoizedState === null && hu(e, t);
				break;
			default: hu(e, t);
		}
	}
	function _u(e, t) {
		if (e.subtreeFlags & 67108864) for (e = e.child; e !== null;) {
			a: {
				var n = e, r = t;
				switch (n.tag) {
					case 4:
						gu(n, r);
						break a;
					case 22:
						n.memoizedState === null && _u(n, r);
						break a;
					default: _u(n, r);
				}
			}
			e = e.sibling;
		}
	}
	function vu(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, vu(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && kt(t)), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	var yu = null, bu = !1;
	function xu(e, t, n) {
		for (n = n.child; n !== null;) Su(e, t, n), n = n.sibling;
	}
	function Su(e, t, n) {
		if (Ye && typeof Ye.onCommitFiberUnmount == "function") try {
			Ye.onCommitFiberUnmount(Je, n);
		} catch {}
		switch (n.tag) {
			case 26:
				nu || Cl(n, t), xu(e, t, n), n.memoizedState ? n.memoizedState.count-- : n.stateNode && !nu && (n = n.stateNode, n.parentNode.removeChild(n));
				break;
			case 27:
				nu || Cl(n, t), El(n);
				var r = yu, i = bu;
				Sp(n.type) && (yu = n.stateNode, bu = !1), xu(e, t, n), gm(n.stateNode, n.type, n.memoizedProps), yu = r, bu = i;
				break;
			case 5: nu || Cl(n, t), El(n);
			case 6:
				if (n.tag === 6 && El(n), r = yu, i = bu, yu = null, xu(e, t, n), yu = r, bu = i, yu !== null) {
					if (bu) try {
						(yu.nodeType === 9 ? yu.body : yu.nodeName === "HTML" ? yu.ownerDocument.body : yu).removeChild(n.stateNode), V = !0;
					} catch (e) {
						ff(n, t, e);
					}
					else try {
						yu.removeChild(n.stateNode), V = !0;
					} catch (e) {
						ff(n, t, e);
					}
				}
				break;
			case 18:
				yu !== null && (bu ? (e = yu, Cp(e.nodeType === 9 ? e.body : e.nodeName === "HTML" ? e.ownerDocument.body : e, n.stateNode), Hh(e)) : Cp(yu, n.stateNode));
				break;
			case 4:
				r = yu, i = bu, yu = n.stateNode.containerInfo, bu = !0, xu(e, t, n), yu = r, bu = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				yl(2, n, t), nu || yl(4, n, t), xu(e, t, n);
				break;
			case 1:
				nu || (Cl(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function" && xl(n, t, r)), xu(e, t, n);
				break;
			case 21:
				xu(e, t, n);
				break;
			case 22:
				nu = (r = nu) || n.memoizedState !== null, xu(e, t, n), nu = r;
				break;
			case 30:
				Cl(n, t), xu(e, t, n);
				break;
			case 7:
				nu || Cl(n, t), xu(e, t, n);
				break;
			default: xu(e, t, n);
		}
	}
	function Cu(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null))) {
			e = e.dehydrated;
			try {
				Hh(e);
			} catch (e) {
				ff(t, t.return, e);
			}
		}
	}
	function wu(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null && (e = e.dehydrated, e !== null)))) try {
			Hh(e);
		} catch (e) {
			ff(t, t.return, e);
		}
	}
	function Tu(e) {
		switch (e.tag) {
			case 31:
			case 13:
			case 19:
				var t = e.stateNode;
				return t === null && (t = e.stateNode = new au()), t;
			case 22: return e = e.stateNode, t = e._retryCache, t === null && (t = e._retryCache = new au()), t;
			default: throw Error(i(435, e.tag));
		}
	}
	function Eu(e, t) {
		var n = Tu(e);
		t.forEach(function(t) {
			if (!n.has(t)) {
				n.add(t);
				var r = _f.bind(null, e, t);
				t.then(r, r);
			}
		});
	}
	function Du(e, t, n) {
		var r = t.deletions;
		if (r !== null) for (var a = 0; a < r.length; a++) {
			var o = r[a], s = e, c = t, l = c;
			a: for (; l !== null;) {
				switch (l.tag) {
					case 27:
						if (Sp(l.type)) {
							yu = l.stateNode, bu = !1;
							break a;
						}
						break;
					case 5:
						yu = l.stateNode, bu = !1;
						break a;
					case 3:
					case 4:
						yu = l.stateNode.containerInfo, bu = !0;
						break a;
				}
				l = l.return;
			}
			if (yu === null) throw Error(i(160));
			Su(s, c, o), yu = null, bu = !1, s = o.alternate, s !== null && (s.return = null), o.return = null;
		}
		if (t.subtreeFlags & 13886) for (t = t.child; t !== null;) ku(t, e, n), t = t.sibling;
	}
	var Ou = null;
	function ku(e, t, n) {
		var r = e.alternate, a = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				if (a & 4 && (r = e.updateQueue, r = r === null ? null : r.events, r !== null)) for (var o = 0; o < r.length; o++) {
					var s = r[o];
					s.ref.impl = s.nextImpl;
				}
				Du(t, e, n), Au(e), a & 4 && (yl(3, e, e.return), vl(3, e), yl(5, e, e.return));
				break;
			case 1:
				Du(t, e, n), Au(e), a & 512 && (nu || r === null || Cl(r, r.return)), a & 64 && tu && (e = e.updateQueue, e !== null && (t = e.callbacks, t !== null && (n = e.shared.hiddenCallbacks, e.shared.hiddenCallbacks = n === null ? t : n.concat(t))));
				break;
			case 26:
				if (o = Ou, Du(t, e, n), Au(e), a & 512 && (nu || r === null || Cl(r, r.return)), a & 4) {
					if (a = r === null ? null : r.memoizedState, n = e.memoizedState, r === null) {
						if (n === null) {
							if (e.stateNode === null) {
								if (tu) e.stateNode = fp(e.type, e.memoizedProps, t.containerInfo, e);
								else {
									a: {
										t = e.type, n = e.memoizedProps, a = o.ownerDocument || o;
										b: switch (t) {
											case "title":
												r = a.getElementsByTagName("title")[0], (!r || r[Dt] || r[xt] || r.namespaceURI === "http://www.w3.org/2000/svg" || r.hasAttribute("itemprop")) && (r = a.createElement(t), a.head.insertBefore(r, a.querySelector("head > title"))), np(r, t, n), r[xt] = e, Mt(r), t = r;
												break a;
											case "link":
												if (o = Gm("link", "href", a).get(t + (n.href || ""))) {
													for (s = 0; s < o.length; s++) if (r = o[s], r.getAttribute("href") === (n.href == null || n.href === "" ? null : n.href) && r.getAttribute("rel") === (n.rel == null ? null : n.rel) && r.getAttribute("title") === (n.title == null ? null : n.title) && r.getAttribute("crossorigin") === (n.crossOrigin == null ? null : n.crossOrigin)) {
														o.splice(s, 1);
														break b;
													}
												}
												r = a.createElement(t), np(r, t, n), a.head.appendChild(r);
												break;
											case "meta":
												if (o = Gm("meta", "content", a).get(t + (n.content || ""))) {
													for (s = 0; s < o.length; s++) if (r = o[s], r.getAttribute("content") === (n.content == null ? null : "" + n.content) && r.getAttribute("name") === (n.name == null ? null : n.name) && r.getAttribute("property") === (n.property == null ? null : n.property) && r.getAttribute("http-equiv") === (n.httpEquiv == null ? null : n.httpEquiv) && r.getAttribute("charset") === (n.charSet == null ? null : n.charSet)) {
														o.splice(s, 1);
														break b;
													}
												}
												r = a.createElement(t), np(r, t, n), a.head.appendChild(r);
												break;
											default: throw Error(i(468, t));
										}
										r[xt] = e, Mt(r), t = r;
									}
									e.stateNode = t;
								}
							} else tu || Km(o, e.type, e.stateNode);
						} else e.stateNode = Bm(o, n, e.memoizedProps);
					} else a === n ? n === null && e.stateNode !== null && Al(e, e.memoizedProps, r.memoizedProps) : (a === null ? (t = r.stateNode, t === null || nu || t.parentNode.removeChild(t)) : a.count--, n === null ? tu || Km(o, e.type, e.stateNode) : Bm(o, n, e.memoizedProps));
				}
				break;
			case 27:
				Du(t, e, n), Au(e), a & 512 && (nu || r === null || Cl(r, r.return)), r !== null && a & 4 && Al(e, e.memoizedProps, r.memoizedProps);
				break;
			case 5:
				if (o = ru, ru = !1, Du(t, e, n), ru = o, Au(e), a & 512 && (nu || r === null || Cl(r, r.return)), e.flags & 32) {
					t = e.stateNode;
					try {
						an(t, ""), V = !0;
					} catch (t) {
						ff(e, e.return, t);
					}
				}
				a & 4 && e.stateNode != null && (t = e.memoizedProps, Al(e, t, r === null ? t : r.memoizedProps)), a & 1024 && (iu = !0);
				break;
			case 6:
				if (Du(t, e, n), Au(e), a & 4) {
					if (e.stateNode === null) throw Error(i(162));
					t = e.memoizedProps, n = e.stateNode;
					try {
						n.nodeValue = t, V = !0;
					} catch (t) {
						ff(e, e.return, t);
					}
				}
				break;
			case 3:
				if (V = !1, Wm = null, o = Ou, Ou = bm(t.containerInfo), Du(t, e, n), Ou = o, Au(e), a & 4 && r !== null && r.memoizedState.isDehydrated) try {
					Hh(t.containerInfo);
				} catch (t) {
					ff(e, e.return, t);
				}
				iu && (iu = !1, ju(e)), V = !1;
				break;
			case 4:
				a = ru, ru = tu, r = Ht(), o = Ou, Ou = bm(e.stateNode.containerInfo), Du(t, e, n), Au(e), Ou = o, V && lu && (uu = !0), V = r, ru = a;
				break;
			case 12:
				Du(t, e, n), Au(e);
				break;
			case 31:
				Du(t, e, n), Au(e), a & 4 && (t = e.updateQueue, t !== null && (e.updateQueue = null, Eu(e, t)));
				break;
			case 13:
				Du(t, e, n), Au(e), e.child.flags & 8192 && e.memoizedState !== null != (r !== null && r.memoizedState !== null) && (pd = ze()), a & 4 && (t = e.updateQueue, t !== null && (e.updateQueue = null, Eu(e, t)));
				break;
			case 22:
				o = e.memoizedState !== null, s = r !== null && r.memoizedState !== null;
				var c = tu, l = nu, u = ru;
				tu = c || o, ru = u || o, nu = l || s, Du(t, e, n), nu = l, ru = u, tu = c, Au(e), a & 8192 && (t = e.stateNode, t._visibility = o ? t._visibility & -2 : t._visibility | 1, !o || r === null || s || tu || nu || (t = s || nu, n = tu, r = nu, tu = o || tu, nu = t, Fu(e, 2), tu = n, nu = r), !o && ru || hu(e, o)), a & 4 && (t = e.updateQueue, t !== null && (n = t.retryQueue, n !== null && (t.retryQueue = null, Eu(e, n))));
				break;
			case 19:
				Du(t, e, n), Au(e), a & 4 && (t = e.updateQueue, t !== null && (e.updateQueue = null, Eu(e, t)));
				break;
			case 30:
				a & 512 && (nu || r === null || Cl(r, r.return)), a = Ht(), o = lu, s = (n & 335544064) === n, c = e.memoizedProps, lu = s && mi(c.default, c.update) !== "none", Du(t, e, n), Au(e), s && r !== null && V && (e.flags |= 4), lu = o, V = a;
				break;
			case 21: break;
			case 7: a & 512 && (nu || r === null || Cl(r, r.return)), r && r.stateNode !== null && (r.stateNode._fragmentFiber = e);
			default: Du(t, e, n), Au(e);
		}
	}
	function Au(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				for (var n, r = e.return; r !== null;) {
					if (jl(r)) {
						n = r;
						break;
					}
					r = r.return;
				}
				r = null;
				for (var a = e.return; a !== null;) {
					if (Ol(a)) {
						var o = a.stateNode;
						r === null ? r = [o] : r.push(o);
					}
					if (Dl(a)) break;
					a = a.return;
				}
				var s = r;
				if (n == null) throw Error(i(160));
				switch (n.tag) {
					case 27:
						var c = n.stateNode;
						Pl(e, Ml(e), c, s);
						break;
					case 5:
						var l = n.stateNode;
						n.flags & 32 && (an(l, ""), n.flags &= -33), Pl(e, Ml(e), l, s);
						break;
					case 3:
					case 4:
						var u = n.stateNode.containerInfo;
						Nl(e, Ml(e), u, s);
						break;
					default: throw Error(i(161));
				}
			} catch (t) {
				ff(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function ju(e) {
		if (e.subtreeFlags & 1024) for (e = e.child; e !== null;) {
			var t = e;
			ju(t), t.tag === 5 && t.flags & 1024 && (t = t.stateNode, gh = !0, t.reset(), gh = !1), e = e.sibling;
		}
	}
	function Mu(e, t) {
		if (t.subtreeFlags & 9270) for (t = t.child; t !== null;) Nu(t, e), t = t.sibling;
		else eu(t, !1);
	}
	function Nu(e, t) {
		var n = e.alternate;
		if (n === null) Kl(e, !1);
		else switch (e.tag) {
			case 3:
				if (du = cu = !1, Bl(), Mu(t, e), !cu && !uu) {
					if (e = zl, e !== null) for (var r = 0; r < e.length; r += 3) {
						n = e[r];
						var i = e[r + 1];
						Ep(n, e[r + 2]), n = n.ownerDocument.documentElement, n !== null && n.animate({
							opacity: [0, 0],
							pointerEvents: ["none", "none"]
						}, {
							duration: 0,
							fill: "forwards",
							pseudoElement: "::view-transition-group(" + i + ")"
						});
					}
					e = t.containerInfo, e = e.nodeType === 9 ? e.documentElement : e.ownerDocument.documentElement, e !== null && e.style.viewTransitionName === "" && (e.style.viewTransitionName = "none", e.animate({
						opacity: [0, 0],
						pointerEvents: ["none", "none"]
					}, {
						duration: 0,
						fill: "forwards",
						pseudoElement: "::view-transition-group(root)"
					}), e.animate({
						width: [0, 0],
						height: [0, 0]
					}, {
						duration: 0,
						fill: "forwards",
						pseudoElement: "::view-transition"
					})), du = !0;
				}
				zl = null;
				break;
			case 5:
				Mu(t, e);
				break;
			case 4:
				r = cu, cu = !1, Mu(t, e), cu && (uu = !0), cu = r;
				break;
			case 22:
				e.memoizedState === null && (n.memoizedState === null ? Mu(t, e) : Kl(e, !1));
				break;
			case 30:
				r = cu, i = Bl(), cu = !1, Mu(t, e), cu && (e.flags |= 4);
				var a = e.memoizedProps, o = e.stateNode;
				t = fi(a, o), o = fi(n.memoizedProps, o);
				var s = mi(a.default, a.update);
				s === "none" ? t = !1 : (a = n.memoizedState, n.memoizedState = null, n = e.child, Vl = 0, t = $l(e, n, t, o, s, a, !0), Vl !== (a === null ? 0 : a.length) && (e.flags |= 32)), e.flags & 4 && t ? (jd(e, e.memoizedProps.onUpdate), zl = i) : i !== null && (i.push.apply(i, zl), zl = i), cu = e.flags & 32 ? !0 : r;
				break;
			default: Mu(t, e);
		}
	}
	function Pu(e, t) {
		if (t.subtreeFlags & 8772) for (t = t.child; t !== null;) mu(e, t.alternate, t), t = t.sibling;
	}
	function Fu(e, t) {
		for (e = e.child; e !== null;) {
			var n = e, r = t;
			switch (n.tag) {
				case 0:
				case 11:
				case 14:
				case 15:
					yl(4, n, n.return), Fu(n, r);
					break;
				case 1:
					Cl(n, n.return);
					var i = n.stateNode;
					typeof i.componentWillUnmount == "function" && xl(n, n.return, i), Fu(n, r);
					break;
				case 27: r & 2 && gm(n.stateNode, n.type, n.memoizedProps);
				case 5:
					Cl(n, n.return), n.tag !== 5 && n.tag !== 27 || El(n), Fu(n, r);
					break;
				case 6:
					El(n);
					break;
				case 26:
					Cl(n, n.return), i = n.stateNode, n.memoizedState !== null || i === null || nu || i.parentNode.removeChild(i), Fu(n, r);
					break;
				case 22:
					n.memoizedState === null && Fu(n, r);
					break;
				case 30:
					Cl(n, n.return), Fu(n, r);
					break;
				case 7: Cl(n, n.return);
				default: Fu(n, r);
			}
			e = e.sibling;
		}
	}
	function Iu(e, t, n) {
		for (n = t.subtreeFlags & 8772 ? n : n & -2, t = t.child; t !== null;) {
			var r = t.alternate, i = e, a = t, o = a.flags, s = !!(n & 1);
			switch (a.tag) {
				case 0:
				case 11:
				case 15:
					Iu(i, a, n), vl(4, a);
					break;
				case 1:
					if (Iu(i, a, n), r = a, i = r.stateNode, typeof i.componentDidMount == "function") try {
						i.componentDidMount();
					} catch (e) {
						ff(r, r.return, e);
					}
					if (r = a, i = r.updateQueue, i !== null) {
						var c = r.stateNode;
						try {
							var l = i.shared.hiddenCallbacks;
							if (l !== null) for (i.shared.hiddenCallbacks = null, i = 0; i < l.length; i++) yo(l[i], c);
						} catch (e) {
							ff(r, r.return, e);
						}
					}
					s && o & 64 && bl(a), Sl(a, a.return);
					break;
				case 27: n & 2 && Fl(a);
				case 5:
					a.tag !== 5 && a.tag !== 27 || Tl(a), Iu(i, a, n), s && r === null && o & 4 && kl(a), Sl(a, a.return);
					break;
				case 6:
					Tl(a);
					break;
				case 26:
					c = a.stateNode, a.memoizedState !== null || c === null || tu || Km(bm(c.ownerDocument), a.type, c), Iu(i, a, n), s && r === null && o & 4 && kl(a), Sl(a, a.return);
					break;
				case 12:
					Iu(i, a, n);
					break;
				case 31:
					Iu(i, a, n), s && o & 4 && Cu(i, a);
					break;
				case 13:
					Iu(i, a, n), s && o & 4 && wu(i, a);
					break;
				case 22:
					a.memoizedState === null && Iu(i, a, n), Sl(a, a.return);
					break;
				case 30:
					Iu(i, a, n), Sl(a, a.return);
					break;
				case 7: Sl(a, a.return);
				default: Iu(i, a, n);
			}
			t = t.sibling;
		}
	}
	function Lu(e, t) {
		var n = null;
		e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), e = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (e = t.memoizedState.cachePool.pool), e !== n && (e != null && e.refCount++, n != null && Oa(n));
	}
	function Ru(e, t) {
		e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && Oa(e));
	}
	function zu(e, t, n, r) {
		var i = (n & 335544064) === n;
		if (t.subtreeFlags & (i ? 10262 : 10256)) for (t = t.child; t !== null;) Bu(e, t, n, r), t = t.sibling;
		else i && Ql(t);
	}
	function Bu(e, t, n, r) {
		var i = (n & 335544064) === n;
		i && t.alternate === null && t.return !== null && t.return.alternate !== null && Zl(t);
		var a = t.flags;
		switch (t.tag) {
			case 0:
			case 11:
			case 15:
				zu(e, t, n, r), a & 2048 && vl(9, t);
				break;
			case 1:
				zu(e, t, n, r);
				break;
			case 3:
				zu(e, t, n, r), i && du && (e = e.containerInfo, e = e.nodeType === 9 ? e.body : e.nodeName === "HTML" ? e.ownerDocument.body : e, e.style.viewTransitionName === "root" && (e.style.viewTransitionName = ""), e = e.ownerDocument.documentElement, e !== null && e.style.viewTransitionName === "none" && (e.style.viewTransitionName = "")), a & 2048 && (a = null, t.alternate !== null && (a = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== a && (t.refCount++, a != null && Oa(a)));
				break;
			case 12:
				if (a & 2048) {
					zu(e, t, n, r), a = t.stateNode;
					try {
						var o = t.memoizedProps, s = o.id, c = o.onPostCommit;
						typeof c == "function" && c(s, t.alternate === null ? "mount" : "update", a.passiveEffectDuration, -0);
					} catch (e) {
						ff(t, t.return, e);
					}
				} else zu(e, t, n, r);
				break;
			case 31:
				zu(e, t, n, r);
				break;
			case 13:
				zu(e, t, n, r);
				break;
			case 23: break;
			case 22:
				o = t.stateNode, s = t.alternate, t.memoizedState === null ? (i && s !== null && s.memoizedState !== null && Zl(t), o._visibility & 2 ? zu(e, t, n, r) : (o._visibility |= 2, Vu(e, t, n, r, !!(t.subtreeFlags & 10256) || !1))) : (i && s !== null && s.memoizedState === null && Zl(s), o._visibility & 2 ? zu(e, t, n, r) : Hu(e, t)), a & 2048 && Lu(s, t);
				break;
			case 24:
				zu(e, t, n, r), a & 2048 && Ru(t.alternate, t);
				break;
			case 30:
				i && (a = t.alternate, a !== null && (Wl(a.child, !0), Wl(t.child, !0))), zu(e, t, n, r);
				break;
			default: zu(e, t, n, r);
		}
	}
	function Vu(e, t, n, r, i) {
		for (i &&= !!(t.subtreeFlags & 10256) || !1, t = t.child; t !== null;) {
			var a = e, o = t, s = n, c = r, l = o.flags;
			switch (o.tag) {
				case 0:
				case 11:
				case 15:
					Vu(a, o, s, c, i), vl(8, o);
					break;
				case 23: break;
				case 22:
					var u = o.stateNode;
					o.memoizedState === null ? (u._visibility |= 2, Vu(a, o, s, c, i)) : u._visibility & 2 ? Vu(a, o, s, c, i) : Hu(a, o), i && l & 2048 && Lu(o.alternate, o);
					break;
				case 24:
					Vu(a, o, s, c, i), i && l & 2048 && Ru(o.alternate, o);
					break;
				default: Vu(a, o, s, c, i);
			}
			t = t.sibling;
		}
	}
	function Hu(e, t) {
		if (t.subtreeFlags & 10256) for (t = t.child; t !== null;) {
			var n = e, r = t, i = r.flags;
			switch (r.tag) {
				case 22:
					Hu(n, r), i & 2048 && Lu(r.alternate, r);
					break;
				case 24:
					Hu(n, r), i & 2048 && Ru(r.alternate, r);
					break;
				default: Hu(n, r);
			}
			t = t.sibling;
		}
	}
	var Uu = 8192;
	function Wu(e, t, n) {
		if (e.subtreeFlags & Uu) for (e = e.child; e !== null;) Gu(e, t, n), e = e.sibling;
	}
	function Gu(e, t, n) {
		switch (e.tag) {
			case 26:
				Wu(e, t, n), e.flags & Uu && (e.memoizedState === null ? (e = e.stateNode, (t & 335544128) === t && Zm(n, e)) : Qm(n, Ou, e.memoizedState, e.memoizedProps));
				break;
			case 5:
				Wu(e, t, n), e.flags & Uu && (e = e.stateNode, (t & 335544128) === t && Zm(n, e));
				break;
			case 3:
			case 4:
				var r = Ou;
				Ou = bm(e.stateNode.containerInfo), Wu(e, t, n), Ou = r;
				break;
			case 22:
				e.memoizedState === null && (r = e.alternate, r !== null && r.memoizedState !== null ? (r = Uu, Uu = 16777216, Wu(e, t, n), Uu = r) : Wu(e, t, n));
				break;
			case 30:
				if ((e.flags & Uu) !== 0 && (r = e.memoizedProps.name, r != null && r !== "auto")) {
					var i = e.stateNode;
					i.paired = null, Ll === null && (Ll = /* @__PURE__ */ new Map()), Ll.set(r, i);
				}
				Wu(e, t, n);
				break;
			default: Wu(e, t, n);
		}
	}
	function Ku(e) {
		var t = e.alternate;
		if (t !== null && (e = t.child, e !== null)) {
			t.child = null;
			do
				t = e.sibling, e.sibling = null, e = t;
			while (e !== null);
		}
	}
	function qu(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				su = r, Xu(r, e);
			}
			Ku(e);
		}
		if (e.subtreeFlags & 10256) for (e = e.child; e !== null;) Ju(e), e = e.sibling;
	}
	function Ju(e) {
		switch (e.tag) {
			case 0:
			case 11:
			case 15:
				qu(e), e.flags & 2048 && yl(9, e, e.return);
				break;
			case 3:
				qu(e);
				break;
			case 12:
				qu(e);
				break;
			case 22:
				var t = e.stateNode;
				e.memoizedState !== null && t._visibility & 2 && (e.return === null || e.return.tag !== 13) ? (t._visibility &= -3, Yu(e)) : qu(e);
				break;
			default: qu(e);
		}
	}
	function Yu(e) {
		var t = e.deletions;
		if (e.flags & 16) {
			if (t !== null) for (var n = 0; n < t.length; n++) {
				var r = t[n];
				su = r, Xu(r, e);
			}
			Ku(e);
		}
		for (e = e.child; e !== null;) {
			switch (t = e, t.tag) {
				case 0:
				case 11:
				case 15:
					yl(8, t, t.return), Yu(t);
					break;
				case 22:
					n = t.stateNode, n._visibility & 2 && (n._visibility &= -3, Yu(t));
					break;
				default: Yu(t);
			}
			e = e.sibling;
		}
	}
	function Xu(e, t) {
		for (; su !== null;) {
			var n = su;
			switch (n.tag) {
				case 0:
				case 11:
				case 15:
					yl(8, n, t);
					break;
				case 23:
				case 22:
					if (n.memoizedState !== null && n.memoizedState.cachePool !== null) {
						var r = n.memoizedState.cachePool.pool;
						r != null && r.refCount++;
					}
					break;
				case 24: Oa(n.memoizedState.cache);
			}
			if (r = n.child, r !== null) r.return = n, su = r;
			else a: for (n = e; su !== null;) {
				r = su;
				var i = r.sibling, a = r.return;
				if (vu(r), r === n) {
					su = null;
					break a;
				}
				if (i !== null) {
					i.return = a, su = i;
					break a;
				}
				su = a;
			}
		}
	}
	var Zu = {
		getCacheForType: function(e) {
			var t = ba(Ea), n = t.data.get(e);
			return n === void 0 && (n = e(), t.data.set(e, n)), n;
		},
		cacheSignal: function() {
			return ba(Ea).controller.signal;
		}
	}, Qu = typeof WeakMap == "function" ? WeakMap : Map, $u = 0, ed = null, q = null, J = 0, Y = 0, X = null, td = !1, nd = !1, rd = !1, id = 0, ad = 0, od = 0, sd = 0, cd = 0, ld = 0, ud = 0, dd = null, Z = null, fd = !1, pd = 0, md = 0, hd = Infinity, gd = null, _d = null, vd = 0, Q = null, yd = null, bd = 0, xd = 0, Sd = null, Cd = null, wd = null, Td = null, Ed = null, Dd = 0, Od = null;
	function kd() {
		return $u & 2 && J !== 0 ? J & -J : I.T === null ? vt() : Nf();
	}
	function Ad() {
		if (ld === 0) {
			if (!(J & 536870912) || W) {
				var e = nt;
				nt <<= 1, !(nt & 3932160) && (nt = 262144), ld = e;
			} else ld = 536870912;
		}
		return e = Eo.current, e !== null && (e.flags |= 32), ld;
	}
	function jd(e, t) {
		if (t != null) {
			var n = e.stateNode, r = n.ref;
			r === null && (r = n.ref = Pp(fi(e.memoizedProps, n))), Td === null && (Td = []), Td.push(t.bind(null, r));
		}
	}
	function Md(e, t, n) {
		(e === ed && (Y === 2 || Y === 9) || e.cancelPendingCommit !== null) && (zd(e, 0), Id(e, J, ld, !1)), dt(e, n), (!($u & 2) || e !== ed) && (e === ed && (!($u & 2) && (sd |= n), ad === 4 && Id(e, J, ld, !1)), Tf(e));
	}
	function Nd(e, t, n) {
		if ($u & 6) throw Error(i(327));
		var r = !n && !(t & 127) && (t & e.expiredLanes) === 0 || ot(e, t), a = r ? qd(e, t) : Gd(e, t, !0), o = r;
		do {
			if (a === 0) {
				nd && !r && Id(e, t, 0, !1);
				break;
			}
			if (n = e.current.alternate, o && !Fd(n)) {
				a = Gd(e, t, !1), o = !1;
				continue;
			}
			if (a === 2) {
				if (o = t, e.errorRecoveryDisabledLanes & o) var s = 0;
				else s = e.pendingLanes & -536870913, s = s === 0 ? s & 536870912 ? 536870912 : 0 : s;
				if (s !== 0) {
					t = s;
					a: {
						var c = e;
						a = dd;
						var l = c.current.memoizedState.isDehydrated;
						if (l && (zd(c, s).flags |= 256), s = Gd(c, s, !1), s !== 2 && s !== 6) {
							if (rd && !l) {
								c.errorRecoveryDisabledLanes |= o, sd |= o, a = 4;
								break a;
							}
							o = Z, Z = a, o !== null && (Z === null ? Z = o : Z.push.apply(Z, o));
						}
						a = s;
					}
					if (o = !1, a !== 2) continue;
				}
			}
			if (a === 1) {
				zd(e, 0), Id(e, t, 0, !0);
				break;
			}
			a: {
				switch (r = e, o = a, o) {
					case 0:
					case 1: throw Error(i(345));
					case 4: if ((t & 4194048) !== t && (t & 62914560) !== t) break;
					case 6:
						Id(r, t, ld, !td);
						break a;
					case 2:
						Z = null;
						break;
					case 3:
					case 5: break;
					default: throw Error(i(329));
				}
				if ((t & 62914560) === t && (a = pd + 300 - ze(), 10 < a)) {
					if (Id(r, t, ld, !td), at(r, 0, !0) !== 0) break a;
					bd = t, r.timeoutHandle = gp(Pd.bind(null, r, n, Z, gd, fd, t, ld, sd, ud, td, o, "Throttled", -0, 0), a);
					break a;
				}
				Pd(r, n, Z, gd, fd, t, ld, sd, ud, td, o, null, -0, 0);
			}
			break;
		} while (1);
		Tf(e);
	}
	function Pd(e, t, n, r, i, a, o, s, c, l, u, d, f, p) {
		e.timeoutHandle = -1;
		var m = t.subtreeFlags, h = (a & 335544064) === a;
		if (d = null, (h || m & 8192 || (m & 16785408) == 16785408) && (d = {
			stylesheets: null,
			count: 0,
			imgCount: 0,
			imgBytes: 0,
			suspenseyImages: [],
			waitingForImages: !0,
			waitingForViewTransition: !1,
			unsuspend: pn
		}, Ll = null, Gu(t, a, d), h && (m = d, h = e.containerInfo, h = (h.nodeType === 9 ? h : h.ownerDocument).__reactViewTransition, h != null && (m.count++, m.waitingForViewTransition = !0, m = nh.bind(m), h.finished.then(m, m))), m = (a & 62914560) === a ? pd - ze() : (a & 4194048) === a ? md - ze() : 0, m = eh(d, m), m !== null)) {
			bd = a, e.cancelPendingCommit = m(ef.bind(null, e, t, a, n, r, i, o, s, c, l, u, d, null, f, p)), Id(e, a, o, !l);
			return;
		}
		ef(e, t, a, n, r, i, o, s, c, l, u, d);
	}
	function Fd(e) {
		for (var t = e;;) {
			var n = t.tag;
			if ((n === 0 || n === 11 || n === 15) && t.flags & 16384 && (n = t.updateQueue, n !== null && (n = n.stores, n !== null))) for (var r = 0; r < n.length; r++) {
				var i = n[r], a = i.getSnapshot;
				i = i.value;
				try {
					if (!Fr(a(), i)) return !1;
				} catch {
					return !1;
				}
			}
			if (n = t.child, t.subtreeFlags & 16384 && n !== null) n.return = t, t = n;
			else {
				if (t === e) break;
				for (; t.sibling === null;) {
					if (t.return === null || t.return === e) return !0;
					t = t.return;
				}
				t.sibling.return = t.return, t = t.sibling;
			}
		}
		return !0;
	}
	function Id(e, t, n, r) {
		t = st(e, t), t &= ~cd, t &= ~sd, e.suspendedLanes |= t, e.pingedLanes &= ~t, r && (e.warmLanes |= t), r = e.expirationTimes;
		for (var i = t; 0 < i;) {
			var a = 31 - Ze(i), o = 1 << a;
			r[a] = -1, i &= ~o;
		}
		n !== 0 && pt(e, n, t);
	}
	function Ld() {
		return $u & 6 ? !0 : (Ef(0, !1), !1);
	}
	function Rd() {
		if (q !== null) {
			if (Y === 0) var e = q.return;
			else e = q, fa = da = null, ts(e), eo = null, to = 0, e = q;
			for (; e !== null;) _l(e.alternate, e), e = e.return;
			q = null;
		}
	}
	function zd(e, t) {
		var n = e.timeoutHandle;
		return n !== -1 && (e.timeoutHandle = -1, _p(n)), n = e.cancelPendingCommit, n !== null && (e.cancelPendingCommit = null, n()), bd = 0, Rd(), ed = e, q = n = ki(e.current, null), J = t, Y = 0, X = null, td = !1, nd = ot(e, t), rd = !1, ud = ld = cd = sd = od = ad = 0, Z = dd = null, fd = !1, id = st(e, t), yi(), n;
	}
	function Bd(e, t) {
		G = null, I.H = dc, t === Wa || t === Ka ? (t = Qa(), Y = 3) : t === Ga ? (t = Qa(), Y = 4) : Y = t === kc ? 8 : typeof t == "object" && t && typeof t.then == "function" ? 6 : 1, X = t, q === null && (ad = 1, Cc(e, Li(t, e.current)));
	}
	function Vd() {
		var e = Eo.current;
		return e === null ? !0 : (J & 4194048) === J ? Do === null : (J & 62914560) === J || J & 536870912 ? e === Do : !1;
	}
	function Hd() {
		var e = I.H;
		return I.H = dc, e === null ? dc : e;
	}
	function Ud() {
		var e = I.A;
		return I.A = Zu, e;
	}
	function Wd() {
		ad = 4, td || (J & 4194048) !== J && Eo.current !== null || (nd = !0), !(od & 134217727) && !(sd & 134217727) || ed === null || Id(ed, J, ld, !1);
	}
	function Gd(e, t, n) {
		var r = $u;
		$u |= 2;
		var i = Hd(), a = Ud();
		(ed !== e || J !== t) && (gd = null, zd(e, t)), t = !1;
		var o = ad;
		a: do
			try {
				if (Y !== 0 && q !== null) {
					var s = q, c = X;
					switch (Y) {
						case 8:
							Rd(), o = 6;
							break a;
						case 3:
						case 2:
						case 9:
						case 6:
							Eo.current === null && (t = !0);
							var l = Y;
							if (Y = 0, X = null, Zd(e, s, c, l), n && nd) {
								o = 0;
								break a;
							}
							break;
						default: l = Y, Y = 0, X = null, Zd(e, s, c, l);
					}
				}
				Kd(), o = ad;
				break;
			} catch (t) {
				Bd(e, t);
			}
		while (1);
		return t && e.shellSuspendCounter++, fa = da = null, $u = r, I.H = i, I.A = a, q === null && (ed = null, J = 0, yi()), o;
	}
	function Kd() {
		for (; q !== null;) Yd(q);
	}
	function qd(e, t) {
		var n = $u;
		$u |= 2;
		var r = Hd(), a = Ud();
		ed !== e || J !== t ? (gd = null, hd = ze() + 500, zd(e, t)) : nd = ot(e, t);
		a: do
			try {
				if (Y !== 0 && q !== null) {
					t = q;
					var o = X;
					b: switch (Y) {
						case 1:
							Y = 0, X = null, Zd(e, t, o, 1);
							break;
						case 2:
						case 9:
							if (Ja(o)) {
								Y = 0, X = null, Xd(t);
								break;
							}
							t = function() {
								Y !== 2 && Y !== 9 || ed !== e || (Y = 7), Tf(e);
							}, o.then(t, t);
							break a;
						case 3:
							Y = 7;
							break a;
						case 4:
							Y = 5;
							break a;
						case 7:
							Ja(o) ? (Y = 0, X = null, Xd(t)) : (Y = 0, X = null, Zd(e, t, o, 7));
							break;
						case 5:
							var s = null;
							switch (q.tag) {
								case 26: s = q.memoizedState;
								case 5:
								case 27:
									var c = q;
									if (s ? Ym(s) : c.stateNode.complete) {
										Y = 0, X = null;
										var l = c.sibling;
										if (l !== null) q = l;
										else {
											var u = c.return;
											u === null ? q = null : (q = u, Qd(u));
										}
										break b;
									}
							}
							Y = 0, X = null, Zd(e, t, o, 5);
							break;
						case 6:
							Y = 0, X = null, Zd(e, t, o, 6);
							break;
						case 8:
							Rd(), ad = 6;
							break a;
						default: throw Error(i(462));
					}
				}
				Jd();
				break;
			} catch (t) {
				Bd(e, t);
			}
		while (1);
		return fa = da = null, I.H = r, I.A = a, $u = n, q === null ? (ed = null, J = 0, yi(), ad) : 0;
	}
	function Jd() {
		for (; q !== null && !Le();) Yd(q);
	}
	function Yd(e) {
		var t = ll(e.alternate, e, id);
		e.memoizedProps = e.pendingProps, t === null ? Qd(e) : q = t;
	}
	function Xd(e) {
		var t = e, n = t.alternate;
		switch (t.tag) {
			case 15:
			case 0:
				t = Uc(n, t, t.pendingProps, t.type, void 0, J);
				break;
			case 11:
				t = Uc(n, t, t.pendingProps, t.type.render, t.ref, J);
				break;
			case 5:
				ts(t);
				var r = t;
				r === Qi && (W ? (aa(r), r.tag === 5 && r.stateNode != null && ($i = r.stateNode)) : (aa(r), W = !0));
			default: _l(n, t), t = q = Ai(t, id), t = ll(n, t, id);
		}
		e.memoizedProps = e.pendingProps, t === null ? Qd(e) : q = t;
	}
	function Zd(e, t, n, r) {
		fa = da = null, ts(t), eo = null, to = 0;
		var i = t.return;
		try {
			if (Oc(e, i, t, n, J)) {
				ad = 1, Cc(e, Li(n, e.current)), q = null;
				return;
			}
		} catch (t) {
			if (i !== null) throw q = i, t;
			ad = 1, Cc(e, Li(n, e.current)), q = null;
			return;
		}
		t.flags & 32768 ? (W || r === 1 ? e = !0 : nd || J & 536870912 ? e = !1 : (td = e = !0, (r === 2 || r === 9 || r === 3 || r === 6) && (r = Eo.current, r !== null && r.tag === 13 && (r.flags |= 16384))), $d(t, e)) : Qd(t);
	}
	function Qd(e) {
		var t = e;
		do {
			if (t.flags & 32768) {
				$d(t, td);
				return;
			}
			e = t.return;
			var n = hl(t.alternate, t, id);
			if (n !== null) {
				q = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				q = t;
				return;
			}
			q = t = e;
		} while (t !== null);
		ad === 0 && (ad = 5);
	}
	function $d(e, t) {
		do {
			var n = gl(e.alternate, e);
			if (n !== null) {
				n.flags &= 32767, q = n;
				return;
			}
			if (n = e.return, n !== null && (n.flags |= 32768, n.subtreeFlags = 0, n.deletions = null), !t && (e = e.sibling, e !== null)) {
				q = e;
				return;
			}
			q = e = n;
		} while (e !== null);
		ad = 6, q = null;
	}
	function ef(e, t, n, r, a, o, s, c, l, u, d, f) {
		e.cancelPendingCommit = null;
		do
			lf();
		while (vd !== 0);
		if ($u & 6) throw Error(i(327));
		if (t !== null) {
			if (t === e.current) throw Error(i(177));
			e === ed && (q = ed = null, J = 0), yd = t, Q = e, bd = n, Sd = a, Cd = r, tf(e, t, n, s, c, l, f);
		}
	}
	function tf(e, t, n, r, i, a, o) {
		var s = t.lanes | t.childLanes;
		if (xd = s, s |= vi, ft(e, n, s, r, i, a), Td = null, (n & 335544064) === n ? (Ed = ja(e), r = 10262) : (Ed = null, r = 10256), (t.subtreeFlags & r) !== 0 || (t.flags & r) !== 0 ? (e.callbackNode = null, e.callbackPriority = 0, vf(Ue, function() {
			return uf(), null;
		})) : (e.callbackNode = null, e.callbackPriority = 0), Il = !1, r = !!(t.flags & 13878), t.subtreeFlags & 13878 || r) {
			r = I.T, I.T = null, i = L.p, L.p = 2, a = $u, $u |= 4;
			try {
				fu(e, t, n);
			} finally {
				$u = a, L.p = i, I.T = r;
			}
		}
		vd = 1, Il ? wd = Mp(o, e.containerInfo, Ed, af, of, rf, sf, uf, nf, null, null) : (af(), of(), sf());
	}
	function nf(e) {
		if (vd !== 0) {
			var t = Q.onRecoverableError;
			t(e, { componentStack: null });
		}
	}
	function rf() {
		vd === 3 && (vd = 0, Nu(yd, Q), vd = 4);
	}
	function af() {
		if (vd === 1) {
			vd = 0;
			var e = Q, t = yd, n = bd, r = !!(t.flags & 13878);
			if (t.subtreeFlags & 13878 || r) {
				r = I.T, I.T = null;
				var i = L.p;
				L.p = 2;
				var a = $u;
				$u |= 4;
				try {
					lu = uu = !1, ku(t, e, n), n = cp;
					var o = Hr(e.containerInfo), s = n.focusedElem, c = n.selectionRange;
					if (o !== s && s && s.ownerDocument && Vr(s.ownerDocument.documentElement, s)) {
						if (c !== null && Ur(s)) {
							var l = c.start, u = c.end;
							if (u === void 0 && (u = l), "selectionStart" in s) s.selectionStart = l, s.selectionEnd = Math.min(u, s.value.length);
							else {
								var d = s.ownerDocument || document, f = d && d.defaultView || window;
								if (f.getSelection) {
									var p = f.getSelection(), m = s.textContent.length, h = Math.min(c.start, m), g = c.end === void 0 ? h : Math.min(c.end, m);
									!p.extend && h > g && (o = g, g = h, h = o);
									var _ = Br(s, h), v = Br(s, g);
									if (_ && v && (p.rangeCount !== 1 || p.anchorNode !== _.node || p.anchorOffset !== _.offset || p.focusNode !== v.node || p.focusOffset !== v.offset)) {
										var y = d.createRange();
										y.setStart(_.node, _.offset), p.removeAllRanges(), h > g ? (p.addRange(y), p.extend(v.node, v.offset)) : (y.setEnd(v.node, v.offset), p.addRange(y));
									}
								}
							}
						}
						for (d = [], p = s; p = p.parentNode;) p.nodeType === 1 && d.push({
							element: p,
							left: p.scrollLeft,
							top: p.scrollTop
						});
						for (typeof s.focus == "function" && s.focus(), s = 0; s < d.length; s++) {
							var b = d[s];
							b.element.scrollLeft = b.left, b.element.scrollTop = b.top;
						}
					}
					gh = !!sp, cp = sp = null;
				} finally {
					$u = a, L.p = i, I.T = r;
				}
			}
			e.current = t, vd = 2;
		}
	}
	function of() {
		if (vd === 2) {
			vd = 0;
			var e = Q, t = yd, n = !!(t.flags & 8772);
			if (t.subtreeFlags & 8772 || n) {
				n = I.T, I.T = null;
				var r = L.p;
				L.p = 2;
				var i = $u;
				$u |= 4;
				try {
					mu(e, t.alternate, t);
				} finally {
					$u = i, L.p = r, I.T = n;
				}
			}
			vd = 3;
		}
	}
	function sf() {
		if (vd === 4 || vd === 3) {
			vd = 0;
			var e = wd;
			wd = null, Re();
			var t = Q, n = yd, r = bd, i = Cd, a = (r & 335544064) === r ? 10262 : 10256;
			if ((n.subtreeFlags & a) !== 0 || (n.flags & a) !== 0 ? vd = 5 : (vd = 0, yd = Q = null, cf(t, t.pendingLanes)), a = t.pendingLanes, a === 0 && (_d = null), _t(r), n = n.stateNode, Ye && typeof Ye.onCommitFiberRoot == "function") try {
				Ye.onCommitFiberRoot(Je, n, void 0, (n.current.flags & 128) == 128);
			} catch {}
			if (i !== null) {
				n = I.T, a = L.p, L.p = 2, I.T = null;
				try {
					for (var o = t.onRecoverableError, s = 0; s < i.length; s++) {
						var c = i[s];
						o(c.value, { componentStack: c.stack });
					}
				} finally {
					I.T = n, L.p = a;
				}
			}
			if (i = Td, o = Ed, Ed = null, i !== null && (Td = null, o === null && (o = []), e !== null)) for (c = 0; c < i.length; c++) n = (0, i[c])(o), n !== void 0 && e.finished.finally(n);
			bd & 3 && lf(), Tf(t), a = t.pendingLanes, r & 261930 && a & 42 ? t === Od ? Dd++ : (Dd = 0, Od = t) : (Dd = 0, Od = null), Ef(0, !1);
		}
	}
	function cf(e, t) {
		(e.pooledCacheLanes &= t) === 0 && (t = e.pooledCache, t != null && (e.pooledCache = null, Oa(t)));
	}
	function lf() {
		return wd !== null && (wd.skipTransition(), wd = null), af(), of(), sf(), uf();
	}
	function uf() {
		if (vd !== 5) return !1;
		var e = Q, t = xd;
		xd = 0;
		var n = _t(bd), r = I.T, a = L.p;
		try {
			L.p = 32 > n ? 32 : n, I.T = null, n = Sd, Sd = null;
			var o = Q, s = bd;
			if (vd = 0, yd = Q = null, bd = 0, $u & 6) throw Error(i(331));
			var c = $u;
			if ($u |= 4, Ju(o.current), Bu(o, o.current, s, n), $u = c, Ef(0, !1), Ye && typeof Ye.onPostCommitFiberRoot == "function") try {
				Ye.onPostCommitFiberRoot(Je, o);
			} catch {}
			return !0;
		} finally {
			L.p = a, I.T = r, cf(e, t);
		}
	}
	function df(e, t, n) {
		t = Li(n, t), t = Tc(e.stateNode, t, 2), e = po(e, t, 2), e !== null && (dt(e, 2), Tf(e));
	}
	function ff(e, t, n) {
		if (e.tag === 3) df(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				df(t, e, n);
				break;
			}
			if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (_d === null || !_d.has(r))) {
					e = Li(n, e), n = Ec(2), r = po(t, n, 2), r !== null && (Dc(n, r, t, e), dt(r, 2), Tf(r));
					break;
				}
			}
			t = t.return;
		}
	}
	function pf(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new Qu();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (rd = !0, i.add(n), e = mf.bind(null, e, t, n), t.then(e, e));
	}
	function mf(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), e.pingedLanes |= e.suspendedLanes & n, e.warmLanes &= ~n, ed === e && (J & n) === n && (ad === 4 || ad === 3 && (J & 62914560) === J && 300 > ze() - pd ? $u & 2 ? cd |= n : zd(e, 0) : cd |= n, ud === J && (ud = 0)), Tf(e);
	}
	function hf(e, t) {
		t === 0 && (t = lt()), e = Si(e, t), e !== null && (dt(e, t), Tf(e));
	}
	function gf(e) {
		var t = e.memoizedState, n = 0;
		t !== null && (n = t.retryLane), hf(e, n);
	}
	function _f(e, t) {
		var n = 0;
		switch (e.tag) {
			case 31:
			case 13:
				var r = e.stateNode, a = e.memoizedState;
				a !== null && (n = a.retryLane);
				break;
			case 19:
				r = e.stateNode;
				break;
			case 22:
				r = e.stateNode._retryCache;
				break;
			default: throw Error(i(314));
		}
		r !== null && r.delete(t), hf(e, n);
	}
	function vf(e, t) {
		return Fe(e, t);
	}
	var yf = null, bf = null, xf = !1, Sf = !1, Cf = !1, wf = 0;
	function Tf(e) {
		e !== bf && e.next === null && (bf === null ? yf = bf = e : bf = bf.next = e), Sf = !0, xf || (xf = !0, Mf());
	}
	function Ef(e, t) {
		if (!Cf && Sf) {
			Cf = !0;
			do
				for (var n = !1, r = yf; r !== null;) {
					if (!t) {
						if (e !== 0) {
							var i = r.pendingLanes;
							if (i === 0) var a = 0;
							else {
								var o = r.suspendedLanes, s = r.pingedLanes;
								a = (1 << 31 - Ze(42 | e) + 1) - 1, a &= i & ~(o & ~s), a = a & 201326741 ? a & 201326741 | 1 : a ? a | 2 : 0;
							}
							a !== 0 && (n = !0, jf(r, a));
						} else a = J, a = at(r, r === ed ? a : 0, r.cancelPendingCommit !== null || r.timeoutHandle !== -1), !(a & 3) || ot(r, a) || (n = !0, jf(r, a));
					}
					r = r.next;
				}
			while (n);
			Cf = !1;
		}
	}
	function Df() {
		Of();
	}
	function Of() {
		Sf = xf = !1;
		var e = 0;
		wf !== 0 && hp() && (e = wf);
		for (var t = ze(), n = null, r = yf; r !== null;) {
			var i = r.next, a = kf(r, t);
			a === 0 ? (r.next = null, n === null ? yf = i : n.next = i, i === null && (bf = n)) : (n = r, (e !== 0 || a & 3) && (Sf = !0)), r = i;
		}
		vd !== 0 && vd !== 5 || Ef(e, !1), wf !== 0 && (wf = 0);
	}
	function kf(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes & -62914561; 0 < a;) {
			var o = 31 - Ze(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = ct(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
		if (t = ed, n = J, n = at(e, e === t ? n : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r = e.callbackNode, n === 0 || e === t && (Y === 2 || Y === 9) || e.cancelPendingCommit !== null) return r !== null && r !== null && Ie(r), e.callbackNode = null, e.callbackPriority = 0;
		if (!(n & 3) || ot(e, n)) {
			if (t = n & -n, t === e.callbackPriority) return t;
			switch (r !== null && Ie(r), _t(n)) {
				case 2:
				case 8:
					n = He;
					break;
				case 32:
					n = Ue;
					break;
				case 268435456:
					n = Ge;
					break;
				default: n = Ue;
			}
			return r = Af.bind(null, e), n = Fe(n, r), e.callbackPriority = t, e.callbackNode = n, t;
		}
		return r !== null && r !== null && Ie(r), e.callbackPriority = 2, e.callbackNode = null, 2;
	}
	function Af(e, t) {
		if (vd !== 0 && vd !== 5) return e.callbackNode = null, e.callbackPriority = 0, null;
		var n = e.callbackNode;
		if (lf() && e.callbackNode !== n) return null;
		var r = J;
		return r = at(e, e === ed ? r : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r === 0 ? null : (Nd(e, r, t), kf(e, ze()), e.callbackNode != null && e.callbackNode === n ? Af.bind(null, e) : null);
	}
	function jf(e, t) {
		if (lf()) return null;
		Nd(e, t, !0);
	}
	function Mf() {
		bp(function() {
			$u & 6 ? Fe(Ve, Df) : Of();
		});
	}
	function Nf() {
		if (wf === 0) {
			var e = Pa;
			e === 0 && (e = tt, tt <<= 1, !(tt & 261888) && (tt = 256)), wf = e;
		}
		return wf;
	}
	function Pf(e) {
		return e == null || typeof e == "symbol" || typeof e == "boolean" ? null : typeof e == "function" ? e : fn(e);
	}
	function Ff(e, t, n, r, i) {
		if (t === "submit" && n && n.stateNode === i) {
			var a = Pf((i[R] || null).action), o = r.submitter;
			o && (t = (t = o[R] || null) ? Pf(t.formAction) : o.getAttribute("formAction"), t !== null && (a = t, o = null));
			var s = new Pn("action", "action", null, r, i);
			e.push({
				event: s,
				listeners: [{
					instance: null,
					listener: function() {
						if (r.defaultPrevented) {
							if (wf !== 0) {
								var e = new FormData(i, o);
								Zs(n, {
									pending: !0,
									data: e,
									method: i.method,
									action: a
								}, null, e);
							}
						} else typeof a == "function" && (s.preventDefault(), e = new FormData(i, o), Zs(n, {
							pending: !0,
							data: e,
							method: i.method,
							action: a
						}, a, e));
					},
					currentTarget: i
				}]
			});
		}
	}
	for (var If = 0; If < li.length; If++) {
		var Lf = li[If];
		ui(Lf.toLowerCase(), "on" + (Lf[0].toUpperCase() + Lf.slice(1)));
	}
	ui(ti, "onAnimationEnd"), ui(ni, "onAnimationIteration"), ui(ri, "onAnimationStart"), ui("dblclick", "onDoubleClick"), ui("focusin", "onFocus"), ui("focusout", "onBlur"), ui(ii, "onTransitionRun"), ui(ai, "onTransitionStart"), ui(oi, "onTransitionCancel"), ui(si, "onTransitionEnd"), Lt("onMouseEnter", ["mouseout", "mouseover"]), Lt("onMouseLeave", ["mouseout", "mouseover"]), Lt("onPointerEnter", ["pointerout", "pointerover"]), Lt("onPointerLeave", ["pointerout", "pointerover"]), It("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), It("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), It("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), It("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), It("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), It("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
	var Rf = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), zf = new Set("beforetoggle cancel close invalid load scroll scrollend toggle".split(" ").concat(Rf));
	function Bf(e, t) {
		t = !!(t & 4);
		for (var n = 0; n < e.length; n++) {
			var r = e[n], i = r.event;
			r = r.listeners;
			a: {
				var a = void 0;
				if (t) for (var o = r.length - 1; 0 <= o; o--) {
					var s = r[o], c = s.instance, l = s.currentTarget;
					if (s = s.listener, c !== a && i.isPropagationStopped()) break a;
					a = s, i.currentTarget = l;
					try {
						a(i);
					} catch (e) {
						hi(e);
					}
					i.currentTarget = null, a = c;
				}
				else for (o = 0; o < r.length; o++) {
					if (s = r[o], c = s.instance, l = s.currentTarget, s = s.listener, c !== a && i.isPropagationStopped()) break a;
					a = s, i.currentTarget = l;
					try {
						a(i);
					} catch (e) {
						hi(e);
					}
					i.currentTarget = null, a = c;
				}
			}
		}
	}
	function $(e, t) {
		var n = t[Ct];
		n === void 0 && (n = t[Ct] = /* @__PURE__ */ new Set());
		var r = e + "__bubble";
		n.has(r) || (Wf(t, e, 2, !1), n.add(r));
	}
	function Vf(e, t, n) {
		var r = 0;
		t && (r |= 4), Wf(n, e, r, t);
	}
	var Hf = "_reactListening" + Math.random().toString(36).slice(2);
	function Uf(e) {
		if (!e[Hf]) {
			e[Hf] = !0, Pt.forEach(function(t) {
				t !== "selectionchange" && (zf.has(t) || Vf(t, !1, e), Vf(t, !0, e));
			});
			var t = e.nodeType === 9 ? e : e.ownerDocument;
			t === null || t[Hf] || (t[Hf] = !0, Vf("selectionchange", !1, t));
		}
	}
	function Wf(e, t, n, r) {
		switch (Ch(t)) {
			case 2:
				var i = _h;
				break;
			case 8:
				i = vh;
				break;
			default: i = yh;
		}
		n = i.bind(null, t, n, e), i = void 0, !Cn || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
			capture: !0,
			passive: i
		}) : i === void 0 ? e.addEventListener(t, n, !1) : e.addEventListener(t, n, { passive: i });
	}
	function Gf(e, t, n, r, i) {
		var a = r;
		if (!(t & 1) && !(t & 2) && r !== null) a: for (;;) {
			if (r === null) return;
			var s = r.tag;
			if (s === 3 || s === 4) {
				var c = r.stateNode.containerInfo;
				if (c === i) break;
				if (s === 4) for (s = r.return; s !== null;) {
					var l = s.tag;
					if ((l === 3 || l === 4) && s.stateNode.containerInfo === i) return;
					s = s.return;
				}
				for (; c !== null;) {
					if (s = At(c), s === null) return;
					if (l = s.tag, l === 5 || l === 6 || l === 26 || l === 27) {
						r = a = s;
						continue a;
					}
					c = c.parentNode;
				}
			}
			r = r.return;
		}
		bn(function() {
			var r = a, i = hn(n), s = [];
			a: {
				var c = ci.get(e);
				if (c !== void 0) {
					var l = Pn, u = e;
					switch (e) {
						case "keypress": if (kn(n) === 0) break a;
						case "keydown":
						case "keyup":
							l = Qn;
							break;
						case "focusin":
							u = "focus", l = Un;
							break;
						case "focusout":
							u = "blur", l = Un;
							break;
						case "beforeblur":
						case "afterblur":
							l = Un;
							break;
						case "click": if (n.button === 2) break a;
						case "auxclick":
						case "dblclick":
						case "mousedown":
						case "mousemove":
						case "mouseup":
						case "mouseout":
						case "mouseover":
						case "contextmenu":
							l = Vn;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							l = Hn;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							l = tr;
							break;
						case ti:
						case ni:
						case ri:
							l = Wn;
							break;
						case si:
							l = nr;
							break;
						case "scroll":
						case "scrollend":
							l = In;
							break;
						case "wheel":
							l = rr;
							break;
						case "copy":
						case "cut":
						case "paste":
							l = Gn;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup":
							l = $n;
							break;
						case "submit":
							l = er;
							break;
						case "toggle":
						case "beforetoggle": l = ir;
					}
					var d = !!(t & 4), f = !d && (e === "scroll" || e === "scrollend"), p = d ? c === null ? null : c + "Capture" : c;
					d = [];
					for (var m = r, h; m !== null;) {
						var g = m;
						if (h = g.stateNode, g = g.tag, g !== 5 && g !== 26 && g !== 27 || h === null || p === null || (g = xn(m, p), g != null && d.push(Kf(m, g, h))), f) break;
						m = m.return;
					}
					0 < d.length && (c = new l(c, u, null, n, i), s.push({
						event: c,
						listeners: d
					}));
				}
			}
			if (!(t & 7)) {
				a: {
					if (l = e === "mouseover" || e === "pointerover", c = e === "mouseout" || e === "pointerout", l && n !== mn && (u = n.relatedTarget || n.fromElement) && (At(u) || u[St])) break a;
					(c || l) && (u = i.window === i ? i : (l = i.ownerDocument) ? l.defaultView || l.parentWindow : window, c ? (l = n.relatedTarget || n.toElement, c = r, l = l ? At(l) : null, l !== null && (f = o(l), d = l.tag, l !== f || d !== 5 && d !== 27 && d !== 6) && (l = null)) : (c = null, l = r), c !== l && (d = Vn, g = "onMouseLeave", p = "onMouseEnter", m = "mouse", (e === "pointerout" || e === "pointerover") && (d = $n, g = "onPointerLeave", p = "onPointerEnter", m = "pointer"), f = c == null ? u : jt(c), h = l == null ? u : jt(l), u = new d(g, m + "leave", c, n, i), u.target = f, u.relatedTarget = h, g = null, At(i) === r && (d = new d(p, m + "enter", l, n, i), d.target = h, d.relatedTarget = f, g = d), f = g, d = c && l ? w(c, l, Jf) : null, c !== null && Yf(s, u, c, d, !1), l !== null && f !== null && Yf(s, f, l, d, !0)));
				}
				a: {
					if (c = r ? jt(r) : window, l = c.nodeName && c.nodeName.toLowerCase(), l === "select" || l === "input" && c.type === "file") var _ = Cr;
					else if (_r(c)) {
						if (wr) _ = Nr;
						else {
							_ = jr;
							var v = Ar;
						}
					} else l = c.nodeName, !l || l.toLowerCase() !== "input" || c.type !== "checkbox" && c.type !== "radio" ? r && ln(r.elementType) && (_ = Cr) : _ = Mr;
					if (_ &&= _(e, r)) {
						vr(s, _, n, i);
						break a;
					}
					v && v(e, c, r);
				}
				switch (v = r ? jt(r) : window, e) {
					case "focusin":
						(_r(v) || v.contentEditable === "true") && (Gr = v, Kr = r, qr = null);
						break;
					case "focusout":
						qr = Kr = Gr = null;
						break;
					case "mousedown":
						Jr = !0;
						break;
					case "contextmenu":
					case "mouseup":
					case "dragend":
						Jr = !1, Yr(s, n, i);
						break;
					case "selectionchange": if (Wr) break;
					case "keydown":
					case "keyup": Yr(s, n, i);
				}
				var y;
				if (or) b: {
					switch (e) {
						case "compositionstart":
							var b = "onCompositionStart";
							break b;
						case "compositionend":
							b = "onCompositionEnd";
							break b;
						case "compositionupdate":
							b = "onCompositionUpdate";
							break b;
					}
					b = void 0;
				}
				else U ? fr(e, n) && (b = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (b = "onCompositionStart");
				b && (lr && n.locale !== "ko" && (U || b !== "onCompositionStart" ? b === "onCompositionEnd" && U && (y = On()) : (Tn = i, En = "value" in Tn ? Tn.value : Tn.textContent, U = !0)), v = qf(r, b), 0 < v.length && (b = new Kn(b, e, null, n, i), s.push({
					event: b,
					listeners: v
				}), y ? b.data = y : (y = pr(n), y !== null && (b.data = y)))), (y = cr ? mr(e, n) : hr(e, n)) && (b = qf(r, "onBeforeInput"), 0 < b.length && (v = new Kn("onBeforeInput", "beforeinput", null, n, i), s.push({
					event: v,
					listeners: b
				}), v.data = y)), Ff(s, e, r, n, i);
			}
			Bf(s, t);
		});
	}
	function Kf(e, t, n) {
		return {
			instance: e,
			listener: t,
			currentTarget: n
		};
	}
	function qf(e, t) {
		for (var n = t + "Capture", r = []; e !== null;) {
			var i = e, a = i.stateNode;
			if (i = i.tag, i !== 5 && i !== 26 && i !== 27 || a === null || (i = xn(e, n), i != null && r.unshift(Kf(e, i, a)), i = xn(e, t), i != null && r.push(Kf(e, i, a))), e.tag === 3) return r;
			e = e.return;
		}
		return [];
	}
	function Jf(e) {
		if (e === null) return null;
		do
			e = e.return;
		while (e && e.tag !== 5 && e.tag !== 27);
		return e || null;
	}
	function Yf(e, t, n, r, i) {
		for (var a = t._reactName, o = []; n !== null && n !== r;) {
			var s = n, c = s.alternate, l = s.stateNode;
			if (s = s.tag, c !== null && c === r) break;
			s !== 5 && s !== 26 && s !== 27 || l === null || (c = l, i ? (l = xn(n, a), l != null && o.unshift(Kf(n, l, c))) : i || (l = xn(n, a), l != null && o.push(Kf(n, l, c)))), n = n.return;
		}
		o.length !== 0 && e.push({
			event: t,
			listeners: o
		});
	}
	var Xf = /\r\n?/g, Zf = /\u0000|\uFFFD/g;
	function Qf(e) {
		return (typeof e == "string" ? e : "" + e).replace(Xf, "\n").replace(Zf, "");
	}
	function $f(e, t) {
		return t = Qf(t), Qf(e) === t;
	}
	function ep(e, t, n, r, a, o) {
		switch (n) {
			case "children":
				if (typeof r == "string") t === "body" || t === "textarea" && r === "" || an(e, r);
				else if (typeof r == "number" || typeof r == "bigint") t !== "body" && an(e, "" + r);
				else return;
				break;
			case "className":
				Ut(e, "class", r);
				break;
			case "tabIndex":
				Ut(e, "tabindex", r);
				break;
			case "dir":
			case "role":
			case "viewBox":
			case "width":
			case "height":
				Ut(e, n, r);
				break;
			case "style":
				cn(e, r, o);
				return;
			case "data": if (t !== "object") {
				Ut(e, "data", r);
				break;
			}
			case "src":
			case "href":
				if (r === "" && (t !== "a" || n !== "href")) {
					e.removeAttribute(n);
					break;
				}
				if (r == null || typeof r == "function" || typeof r == "symbol" || typeof r == "boolean") {
					e.removeAttribute(n);
					break;
				}
				r = fn(r), e.setAttribute(n, r);
				break;
			case "action":
			case "formAction":
				if (typeof r == "function") {
					e.setAttribute(n, "javascript:throw new Error('A React form was unexpectedly submitted. If you called form.submit() manually, consider using form.requestSubmit() instead. If you\\'re trying to use event.stopPropagation() in a submit event handler, consider also calling event.preventDefault().')");
					break;
				}
				if (typeof o == "function" && (n === "formAction" ? (t !== "input" && ep(e, t, "name", a.name, a, null), ep(e, t, "formEncType", a.formEncType, a, null), ep(e, t, "formMethod", a.formMethod, a, null), ep(e, t, "formTarget", a.formTarget, a, null)) : (ep(e, t, "encType", a.encType, a, null), ep(e, t, "method", a.method, a, null), ep(e, t, "target", a.target, a, null))), r == null || typeof r == "symbol" || typeof r == "boolean") {
					e.removeAttribute(n);
					break;
				}
				r = fn(r), e.setAttribute(n, r);
				break;
			case "onClick":
				r != null && (e.onclick = pn);
				return;
			case "onScroll":
				r != null && $("scroll", e);
				return;
			case "onScrollEnd":
				r != null && $("scrollend", e);
				return;
			case "dangerouslySetInnerHTML":
				if (r != null) {
					if (typeof r != "object" || !("__html" in r)) throw Error(i(61));
					if (n = r.__html, n != null) {
						if (a.children != null) throw Error(i(60));
						o?.__html !== n && (e.innerHTML = n);
					}
				}
				break;
			case "multiple":
				e.multiple = r && typeof r != "function" && typeof r != "symbol";
				break;
			case "muted":
				e.muted = r && typeof r != "function" && typeof r != "symbol";
				break;
			case "suppressContentEditableWarning":
			case "suppressHydrationWarning":
			case "defaultValue":
			case "defaultChecked":
			case "innerHTML":
			case "ref": break;
			case "autoFocus": break;
			case "xlinkHref":
				if (r == null || typeof r == "function" || typeof r == "boolean" || typeof r == "symbol") {
					e.removeAttribute("xlink:href");
					break;
				}
				n = fn(r), e.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", n);
				break;
			case "contentEditable":
			case "spellCheck":
			case "draggable":
			case "value":
			case "autoReverse":
			case "externalResourcesRequired":
			case "focusable":
			case "preserveAlpha":
				r != null && typeof r != "function" && typeof r != "symbol" ? e.setAttribute(n, r) : e.removeAttribute(n);
				break;
			case "inert":
			case "allowFullScreen":
			case "async":
			case "autoPlay":
			case "controls":
			case "credentialless":
			case "default":
			case "defer":
			case "disabled":
			case "disablePictureInPicture":
			case "disableRemotePlayback":
			case "formNoValidate":
			case "hidden":
			case "loop":
			case "noModule":
			case "noValidate":
			case "open":
			case "playsInline":
			case "readOnly":
			case "required":
			case "reversed":
			case "scoped":
			case "seamless":
			case "itemScope":
				r && typeof r != "function" && typeof r != "symbol" ? e.setAttribute(n, "") : e.removeAttribute(n);
				break;
			case "capture":
			case "download":
				!0 === r ? e.setAttribute(n, "") : !1 !== r && r != null && typeof r != "function" && typeof r != "symbol" ? e.setAttribute(n, r) : e.removeAttribute(n);
				break;
			case "cols":
			case "rows":
			case "size":
			case "span":
				r != null && typeof r != "function" && typeof r != "symbol" && !isNaN(r) && 1 <= r ? e.setAttribute(n, r) : e.removeAttribute(n);
				break;
			case "rowSpan":
			case "start":
				r == null || typeof r == "function" || typeof r == "symbol" || isNaN(r) ? e.removeAttribute(n) : e.setAttribute(n, r);
				break;
			case "popover":
				$("beforetoggle", e), $("toggle", e), H(e, "popover", r);
				break;
			case "xlinkActuate":
				Wt(e, "http://www.w3.org/1999/xlink", "xlink:actuate", r);
				break;
			case "xlinkArcrole":
				Wt(e, "http://www.w3.org/1999/xlink", "xlink:arcrole", r);
				break;
			case "xlinkRole":
				Wt(e, "http://www.w3.org/1999/xlink", "xlink:role", r);
				break;
			case "xlinkShow":
				Wt(e, "http://www.w3.org/1999/xlink", "xlink:show", r);
				break;
			case "xlinkTitle":
				Wt(e, "http://www.w3.org/1999/xlink", "xlink:title", r);
				break;
			case "xlinkType":
				Wt(e, "http://www.w3.org/1999/xlink", "xlink:type", r);
				break;
			case "xmlBase":
				Wt(e, "http://www.w3.org/XML/1998/namespace", "xml:base", r);
				break;
			case "xmlLang":
				Wt(e, "http://www.w3.org/XML/1998/namespace", "xml:lang", r);
				break;
			case "xmlSpace":
				Wt(e, "http://www.w3.org/XML/1998/namespace", "xml:space", r);
				break;
			case "is":
				H(e, "is", r);
				break;
			case "innerText":
			case "textContent": return;
			default: if (!(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") n = un.get(n) || n, H(e, n, r);
			else return;
		}
		V = !0;
	}
	function tp(e, t, n, r, a, o) {
		switch (n) {
			case "style":
				cn(e, r, o);
				return;
			case "dangerouslySetInnerHTML":
				if (r != null) {
					if (typeof r != "object" || !("__html" in r)) throw Error(i(61));
					if (n = r.__html, n != null) {
						if (a.children != null) throw Error(i(60));
						o?.__html !== n && (e.innerHTML = n);
					}
				}
				break;
			case "children":
				if (typeof r == "string") an(e, r);
				else if (typeof r == "number" || typeof r == "bigint") an(e, "" + r);
				else return;
				break;
			case "onScroll":
				r != null && $("scroll", e);
				return;
			case "onScrollEnd":
				r != null && $("scrollend", e);
				return;
			case "onClick":
				r != null && (e.onclick = pn);
				return;
			case "suppressContentEditableWarning":
			case "suppressHydrationWarning":
			case "innerHTML":
			case "ref": return;
			case "innerText":
			case "textContent": return;
			default:
				if (!Ft.hasOwnProperty(n)) a: {
					if (n[0] === "o" && n[1] === "n" && (a = n.endsWith("Capture"), o = n.slice(2, a ? n.length - 7 : void 0), t = e[R] || null, t = t == null ? null : t[n], typeof t == "function" && e.removeEventListener(o, t, a), typeof r == "function")) {
						typeof t != "function" && t !== null && (n in e ? e[n] = null : e.hasAttribute(n) && e.removeAttribute(n)), e.addEventListener(o, r, a);
						break a;
					}
					V = !0, n in e ? e[n] = r : !0 === r ? e.setAttribute(n, "") : H(e, n, r);
				}
				return;
		}
		V = !0;
	}
	function np(e, t, n) {
		switch (t) {
			case "div":
			case "span":
			case "svg":
			case "path":
			case "a":
			case "g":
			case "p":
			case "li": break;
			case "img":
				$("error", e), $("load", e);
				var r = !1, a = !1, o;
				for (o in n) if (n.hasOwnProperty(o)) {
					var s = n[o];
					if (s != null) switch (o) {
						case "src":
							r = !0;
							break;
						case "srcSet":
							a = !0;
							break;
						case "children":
						case "dangerouslySetInnerHTML": throw Error(i(137, t));
						default: ep(e, t, o, s, n, null);
					}
				}
				a && ep(e, t, "srcSet", n.srcSet, n, null), r && ep(e, t, "src", n.src, n, null);
				return;
			case "input":
				$("invalid", e);
				var c = o = s = a = null, l = null, u = null;
				for (r in n) if (n.hasOwnProperty(r)) {
					var d = n[r];
					if (d != null) switch (r) {
						case "name":
							a = d;
							break;
						case "type":
							s = d;
							break;
						case "checked":
							l = d;
							break;
						case "defaultChecked":
							u = d;
							break;
						case "value":
							o = d;
							break;
						case "defaultValue":
							c = d;
							break;
						case "children":
						case "dangerouslySetInnerHTML":
							if (d != null) throw Error(i(137, t));
							break;
						default: ep(e, t, r, d, n, null);
					}
				}
				$t(e, o, c, l, u, s, a, !1);
				return;
			case "select":
				for (a in $("invalid", e), r = s = o = null, n) if (n.hasOwnProperty(a) && (c = n[a], c != null)) switch (a) {
					case "value":
						o = c;
						break;
					case "defaultValue":
						s = c;
						break;
					case "multiple": r = c;
					default: ep(e, t, a, c, n, null);
				}
				t = o, n = s, e.multiple = !!r, t == null ? n != null && tn(e, !!r, n, !0) : tn(e, !!r, t, !1);
				return;
			case "textarea":
				for (s in $("invalid", e), o = a = r = null, n) if (n.hasOwnProperty(s) && (c = n[s], c != null)) switch (s) {
					case "value":
						r = c;
						break;
					case "defaultValue":
						a = c;
						break;
					case "children":
						o = c;
						break;
					case "dangerouslySetInnerHTML":
						if (c != null) throw Error(i(91));
						break;
					default: ep(e, t, s, c, n, null);
				}
				rn(e, r, a, o);
				return;
			case "option":
				for (l in n) if (n.hasOwnProperty(l) && (r = n[l], r != null)) switch (l) {
					case "selected":
						e.selected = r && typeof r != "function" && typeof r != "symbol";
						break;
					default: ep(e, t, l, r, n, null);
				}
				return;
			case "dialog":
				$("beforetoggle", e), $("toggle", e), $("cancel", e), $("close", e);
				break;
			case "iframe":
			case "object":
				$("load", e);
				break;
			case "video":
			case "audio":
				for (r = 0; r < Rf.length; r++) $(Rf[r], e);
				break;
			case "image":
				$("error", e), $("load", e);
				break;
			case "details":
				$("toggle", e);
				break;
			case "embed":
			case "source":
			case "link": $("error", e), $("load", e);
			case "area":
			case "base":
			case "br":
			case "col":
			case "hr":
			case "keygen":
			case "meta":
			case "param":
			case "track":
			case "wbr":
			case "menuitem":
				for (u in n) if (n.hasOwnProperty(u) && (r = n[u], r != null)) switch (u) {
					case "children":
					case "dangerouslySetInnerHTML": throw Error(i(137, t));
					default: ep(e, t, u, r, n, null);
				}
				return;
			default: if (ln(t)) {
				for (d in n) n.hasOwnProperty(d) && (r = n[d], r !== void 0 && tp(e, t, d, r, n, void 0));
				return;
			}
		}
		for (c in n) n.hasOwnProperty(c) && (r = n[c], r != null && ep(e, t, c, r, n, null));
	}
	var rp = {};
	function ip(e, t, n, r) {
		switch (t) {
			case "div":
			case "span":
			case "svg":
			case "path":
			case "a":
			case "g":
			case "p":
			case "li": break;
			case "input":
				var a = null, o = null, s = null, c = null, l = null, u = null, d = null;
				for (m in n) {
					var f = n[m];
					if (n.hasOwnProperty(m) && f != null) switch (m) {
						case "checked": break;
						case "value": break;
						case "defaultValue": l = f;
						default: r.hasOwnProperty(m) || ep(e, t, m, null, r, f);
					}
				}
				for (var p in r) {
					var m = r[p];
					if (f = n[p], r.hasOwnProperty(p) && (m != null || f != null)) switch (p) {
						case "type":
							m !== f && (V = !0), o = m;
							break;
						case "name":
							m !== f && (V = !0), a = m;
							break;
						case "checked":
							m !== f && (V = !0), u = m;
							break;
						case "defaultChecked":
							m !== f && (V = !0), d = m;
							break;
						case "value":
							m !== f && (V = !0), s = m;
							break;
						case "defaultValue":
							m !== f && (V = !0), c = m;
							break;
						case "children":
						case "dangerouslySetInnerHTML":
							if (m != null) throw Error(i(137, t));
							break;
						default: m !== f && ep(e, t, p, m, r, f);
					}
				}
				Qt(e, s, c, l, u, d, o, a);
				return;
			case "select":
				for (o in m = s = c = p = null, n) if (l = n[o], n.hasOwnProperty(o) && l != null) switch (o) {
					case "value": break;
					case "multiple": m = l;
					default: r.hasOwnProperty(o) || ep(e, t, o, null, r, l);
				}
				for (a in r) if (o = r[a], l = n[a], r.hasOwnProperty(a) && (o != null || l != null)) switch (a) {
					case "value":
						o !== l && (V = !0), p = o;
						break;
					case "defaultValue":
						o !== l && (V = !0), c = o;
						break;
					case "multiple": o !== l && (V = !0), s = o;
					default: o !== l && ep(e, t, a, o, r, l);
				}
				t = c, n = s, r = m, p == null ? !!r != !!n && (t == null ? tn(e, !!n, n ? [] : "", !1) : tn(e, !!n, t, !0)) : tn(e, !!n, p, !1);
				return;
			case "textarea":
				for (c in m = p = null, n) if (a = n[c], n.hasOwnProperty(c) && a != null && !r.hasOwnProperty(c)) switch (c) {
					case "value": break;
					case "children": break;
					default: ep(e, t, c, null, r, a);
				}
				for (s in r) if (a = r[s], o = n[s], r.hasOwnProperty(s) && (a != null || o != null)) switch (s) {
					case "value":
						a !== o && (V = !0), p = a;
						break;
					case "defaultValue":
						a !== o && (V = !0), m = a;
						break;
					case "children": break;
					case "dangerouslySetInnerHTML":
						if (a != null) throw Error(i(91));
						break;
					default: a !== o && ep(e, t, s, a, r, o);
				}
				nn(e, p, m);
				return;
			case "option":
				for (var h in n) if (p = n[h], n.hasOwnProperty(h) && p != null && !r.hasOwnProperty(h)) switch (h) {
					case "selected":
						e.selected = !1;
						break;
					default: ep(e, t, h, null, r, p);
				}
				for (l in r) if (p = r[l], m = n[l], r.hasOwnProperty(l) && p !== m && (p != null || m != null)) switch (l) {
					case "selected":
						p !== m && (V = !0), e.selected = p && typeof p != "function" && typeof p != "symbol";
						break;
					default: ep(e, t, l, p, r, m);
				}
				return;
			case "img":
			case "link":
			case "area":
			case "base":
			case "br":
			case "col":
			case "embed":
			case "hr":
			case "keygen":
			case "meta":
			case "param":
			case "source":
			case "track":
			case "wbr":
			case "menuitem":
				for (var g in n) p = n[g], n.hasOwnProperty(g) && p != null && !r.hasOwnProperty(g) && ep(e, t, g, null, r, p);
				for (u in r) if (p = r[u], m = n[u], r.hasOwnProperty(u) && p !== m && (p != null || m != null)) switch (u) {
					case "children":
					case "dangerouslySetInnerHTML":
						if (p != null) throw Error(i(137, t));
						break;
					default: ep(e, t, u, p, r, m);
				}
				return;
			default: if (ln(t)) {
				for (var _ in n) p = n[_], n.hasOwnProperty(_) && p !== void 0 && !r.hasOwnProperty(_) && tp(e, t, _, void 0, r, p);
				for (d in r) p = r[d], m = n[d], !r.hasOwnProperty(d) || p === m || p === void 0 && m === void 0 || tp(e, t, d, p, r, m);
				return;
			}
		}
		for (var v in n) p = n[v], n.hasOwnProperty(v) && p != null && !r.hasOwnProperty(v) && ep(e, t, v, null, r, p);
		for (f in r) p = r[f], m = n[f], !r.hasOwnProperty(f) || p === m || p == null && m == null || ep(e, t, f, p, r, m);
	}
	function ap(e) {
		switch (e) {
			case "css":
			case "script":
			case "font":
			case "img":
			case "image":
			case "input":
			case "link": return !0;
			default: return !1;
		}
	}
	function op() {
		if (typeof performance.getEntriesByType == "function") {
			for (var e = 0, t = 0, n = performance.getEntriesByType("resource"), r = 0; r < n.length; r++) {
				var i = n[r], a = i.transferSize, o = i.initiatorType, s = i.duration;
				if (a && s && ap(o)) {
					for (o = 0, s = i.responseEnd, r += 1; r < n.length; r++) {
						var c = n[r], l = c.startTime;
						if (l > s) break;
						var u = c.transferSize, d = c.initiatorType;
						u && ap(d) && (c = c.responseEnd, o += u * (c < s ? 1 : (s - l) / (c - l)));
					}
					if (--r, t += 8 * (a + o) / (i.duration / 1e3), e++, 10 < e) break;
				}
			}
			if (0 < e) return t / e / 1e6;
		}
		return navigator.connection && (e = navigator.connection.downlink, typeof e == "number") ? e : 5;
	}
	var sp = null, cp = null;
	function lp(e) {
		return e.nodeType === 9 ? e : e.ownerDocument;
	}
	function up(e) {
		switch (e) {
			case "http://www.w3.org/2000/svg": return 1;
			case "http://www.w3.org/1998/Math/MathML": return 2;
			default: return 0;
		}
	}
	function dp(e, t) {
		if (e === 0) switch (t) {
			case "svg": return 1;
			case "math": return 2;
			default: return 0;
		}
		return e === 1 && t === "foreignObject" ? 0 : e;
	}
	function fp(e, t, n, r) {
		return n = lp(n).createElement(e), n[xt] = r, n[R] = t, np(n, e, t), Mt(n), n;
	}
	function pp(e, t) {
		return e === "textarea" || e === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.children == "bigint" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
	}
	var mp = null;
	function hp() {
		var e = window.event;
		return e && e.type === "popstate" ? e !== mp && (mp = e, !0) : (mp = null, !1);
	}
	var gp = typeof setTimeout == "function" ? setTimeout : void 0, _p = typeof clearTimeout == "function" ? clearTimeout : void 0, vp = typeof Promise == "function" ? Promise : void 0, yp = typeof requestAnimationFrame == "function" ? requestAnimationFrame : gp, bp = typeof queueMicrotask == "function" ? queueMicrotask : vp === void 0 ? gp : function(e) {
		return vp.resolve(null).then(e).catch(xp);
	};
	function xp(e) {
		setTimeout(function() {
			throw e;
		});
	}
	function Sp(e) {
		return e === "head";
	}
	function Cp(e, t) {
		var n = t, r = 0;
		do {
			var i = n.nextSibling;
			if (e.removeChild(n), i && i.nodeType === 8) {
				if (n = i.data, n === "/$" || n === "/&") {
					if (r === 0) {
						e.removeChild(i), Hh(t);
						return;
					}
					r--;
				} else if (n === "$" || n === "$?" || n === "$~" || n === "$!" || n === "&") r++;
				else if (n === "html") _m(e.ownerDocument.documentElement);
				else if (n === "head") {
					n = e.ownerDocument.head, _m(n);
					for (var a = n.firstChild; a;) {
						var o = a.nextSibling, s = a.nodeName;
						a[Dt] || s === "SCRIPT" || s === "STYLE" || s === "LINK" && a.rel.toLowerCase() === "stylesheet" || n.removeChild(a), a = o;
					}
				} else n === "body" && _m(e.ownerDocument.body);
			}
			n = i;
		} while (n);
		Hh(t);
	}
	function wp(e, t) {
		var n = e;
		e = 0;
		do {
			var r = n.nextSibling;
			if (n.nodeType === 1 ? t ? (n._stashedDisplay = n.style.display, n.style.display = "none") : (n.style.display = n._stashedDisplay || "", n.getAttribute("style") === "" && n.removeAttribute("style")) : n.nodeType === 3 && (t ? (n._stashedText = n.nodeValue, n.nodeValue = "") : n.nodeValue = n._stashedText || ""), r && r.nodeType === 8) {
				if (n = r.data, n === "/$") {
					if (e === 0) break;
					e--;
				} else n !== "$" && n !== "$?" && n !== "$~" && n !== "$!" || e++;
			}
			n = r;
		} while (n);
	}
	function Tp(e, t, n) {
		if (t = CSS.escape(t) === t ? t : "r-" + btoa(t).replace(/=/g, ""), e.style.viewTransitionName = t, n != null && (e.style.viewTransitionClass = n), n = getComputedStyle(e), n.display === "inline") {
			if (t = e.getClientRects(), t.length === 1) var r = 1;
			else for (var i = r = 0; i < t.length; i++) {
				var a = t[i];
				0 < a.width && 0 < a.height && r++;
			}
			r === 1 && (e = e.style, e.display = t.length === 1 ? "inline-block" : "block", e.marginTop = "-" + n.paddingTop, e.marginBottom = "-" + n.paddingBottom);
		}
	}
	function Ep(e, t) {
		e = e.style, t = t.style;
		var n = t == null ? null : t.hasOwnProperty("viewTransitionName") ? t.viewTransitionName : t.hasOwnProperty("view-transition-name") ? t["view-transition-name"] : null;
		e.viewTransitionName = n == null || typeof n == "boolean" ? "" : ("" + n).trim(), n = t == null ? null : t.hasOwnProperty("viewTransitionClass") ? t.viewTransitionClass : t.hasOwnProperty("view-transition-class") ? t["view-transition-class"] : null, e.viewTransitionClass = n == null || typeof n == "boolean" ? "" : ("" + n).trim(), e.display === "inline-block" && (t == null ? e.display = e.margin = "" : (n = t.display, e.display = n == null || typeof n == "boolean" ? "" : n, n = t.margin, n == null ? (n = t.hasOwnProperty("marginTop") ? t.marginTop : t["margin-top"], e.marginTop = n == null || typeof n == "boolean" ? "" : n, t = t.hasOwnProperty("marginBottom") ? t.marginBottom : t["margin-bottom"], e.marginBottom = t == null || typeof t == "boolean" ? "" : t) : e.margin = n));
	}
	function Dp(e, t, n) {
		return n = n.ownerDocument.defaultView, {
			rect: e,
			abs: t.position === "absolute" || t.position === "fixed",
			clip: t.clipPath !== "none" || t.overflow !== "visible" || t.filter !== "none" || t.mask !== "none" || t.mask !== "none" || t.borderRadius !== "0px",
			view: 0 <= e.bottom && 0 <= e.right && e.top <= n.innerHeight && e.left <= n.innerWidth
		};
	}
	function Op(e) {
		return Dp(e.getBoundingClientRect(), getComputedStyle(e), e);
	}
	function kp(e) {
		var t = e.getBoundingClientRect();
		t = new DOMRect(t.x + 2e4, t.y + 2e4, t.width, t.height);
		var n = getComputedStyle(e);
		return Dp(t, n, e);
	}
	function Ap(e) {
		return e.documentElement.clientHeight;
	}
	function jp(e) {
		this.addEventListener("load", e), this.addEventListener("error", e);
	}
	function Mp(e, t, n, r, i, a, o, s, c) {
		var l = t.nodeType === 9 ? t : t.ownerDocument;
		try {
			var u = l.startViewTransition({
				update: function() {
					var t = l.defaultView, n = t.navigation && t.navigation.transition, o = l.fonts.status;
					r();
					var s = [];
					if (o === "loaded" && (Ap(l), l.fonts.status === "loading" && s.push(l.fonts.ready)), o = s.length, e !== null) for (var c = e.suspenseyImages, u = 0, d = 0; d < c.length; d++) {
						var f = c[d];
						if (!f.complete) {
							var p = f.getBoundingClientRect();
							if (0 < p.bottom && 0 < p.right && p.top < t.innerHeight && p.left < t.innerWidth) {
								if (u += Xm(f), u > $m) {
									s.length = o;
									break;
								}
								f = new Promise(jp.bind(f)), s.push(f);
							}
						}
					}
					if (0 < s.length) return t = Promise.race([Promise.all(s), new Promise(function(e) {
						return setTimeout(e, 500);
					})]).then(i, i), (n ? Promise.allSettled([n.finished, t]) : t).then(a, a);
					if (i(), n) return n.finished.then(a, a);
					a();
				},
				types: n
			});
			l.__reactViewTransition = u;
			var d = [];
			return u.ready.then(function() {
				for (var e = l.documentElement.getAnimations({ subtree: !0 }), t = 0; t < e.length; t++) {
					var n = e[t], r = n.effect, i = r.pseudoElement;
					if (i != null && i.startsWith("::view-transition")) {
						d.push(n), n = r.getKeyframes();
						for (var a = i = void 0, s = !0, c = 0; c < n.length; c++) {
							var u = n[c], f = u.width;
							if (i === void 0) i = f;
							else if (i !== f) {
								s = !1;
								break;
							}
							if (f = u.height, a === void 0) a = f;
							else if (a !== f) {
								s = !1;
								break;
							}
							delete u.width, delete u.height, u.transform === "none" && delete u.transform;
						}
						s && i !== void 0 && a !== void 0 && (r.setKeyframes(n), s = getComputedStyle(r.target, r.pseudoElement), s.width !== i || s.height !== a) && (s = n[0], s.width = i, s.height = a, s = n[n.length - 1], s.width = i, s.height = a, r.setKeyframes(n));
					}
				}
				o();
			}, function(e) {
				l.__reactViewTransition === u && (l.__reactViewTransition = null);
				try {
					if (typeof e == "object" && e) switch (e.name) {
						case "InvalidStateError": (e.message === "View transition was skipped because document visibility state is hidden." || e.message === "Skipping view transition because document visibility state has become hidden." || e.message === "Skipping view transition because viewport size changed." || e.message === "Transition was aborted because of invalid state") && (e = null);
					}
					e !== null && c(e);
				} finally {
					r(), i(), o();
				}
			}), u.finished.finally(function() {
				for (var e = 0; e < d.length; e++) d[e].cancel();
				l.__reactViewTransition === u && (l.__reactViewTransition = null), s();
			}), u;
		} catch {
			return r(), i(), o(), null;
		}
	}
	function Np(e, t) {
		this._scope = document.documentElement, this._selector = "::view-transition-" + e + "(" + t + ")";
	}
	Np.prototype.animate = function(e, t) {
		return t = typeof t == "number" ? { duration: t } : T({}, t), t.pseudoElement = this._selector, this._scope.animate(e, t);
	}, Np.prototype.getAnimations = function() {
		for (var e = this._scope, t = this._selector, n = e.getAnimations({ subtree: !0 }), r = [], i = 0; i < n.length; i++) {
			var a = n[i].effect;
			a !== null && a.target === e && a.pseudoElement === t && r.push(n[i]);
		}
		return r;
	}, Np.prototype.getComputedStyle = function() {
		return getComputedStyle(this._scope, this._selector);
	};
	function Pp(e) {
		return {
			name: e,
			group: new Np("group", e),
			imagePair: new Np("image-pair", e),
			old: new Np("old", e),
			new: new Np("new", e)
		};
	}
	function Fp(e) {
		this._fragmentFiber = e, this._observers = this._eventListeners = null;
	}
	Fp.prototype.addEventListener = function(e, t, n) {
		var r = null, i = null;
		if (!(n != null && typeof n != "boolean" && (r = n.signal || null, r !== null && r.aborted))) {
			this._eventListeners === null && (this._eventListeners = []);
			var a = this._eventListeners;
			if (Bp(a, e, t, n) === -1) {
				var o = this, s = t;
				n != null && typeof n != "boolean" && !0 === n.once && (s = function(r) {
					o.removeEventListener(e, t, n), typeof t == "function" ? t.call(this, r) : t.handleEvent(r);
				}), r !== null && (i = o.removeEventListener.bind(o, e, t, n), r.addEventListener("abort", i, { once: !0 }), i = r.removeEventListener.bind(r, "abort", i)), r = Rp(n), a.push({
					type: e,
					listener: t,
					optionsOrUseCapture: n,
					attachedListener: s,
					cleanup: i
				}), f(this._fragmentFiber.child, !1, Ip, e, s, r);
			}
			this._eventListeners = a;
		}
	};
	function Ip(e, t, n, r) {
		return v(e).addEventListener(t, n, r), !1;
	}
	Fp.prototype.removeEventListener = function(e, t, n) {
		var r = this._eventListeners;
		if (r !== null && (t = Bp(r, e, t, n), t !== -1)) {
			var i = r[t];
			n = i.attachedListener;
			var a = i.cleanup;
			i = Rp(i.optionsOrUseCapture), f(this._fragmentFiber.child, !1, Lp, e, n, i), r.splice(t, 1), a !== null && a();
		}
	};
	function Lp(e, t, n, r) {
		return v(e).removeEventListener(t, n, r), !1;
	}
	function Rp(e) {
		return e != null && typeof e != "boolean" && (!0 === e.once || e.signal instanceof AbortSignal) ? {
			capture: e.capture,
			passive: e.passive
		} : e;
	}
	function zp(e) {
		return e == null ? "c=0" : typeof e == "boolean" ? "c=" + (e ? "1" : "0") : "c=" + (e.capture ? "1" : "0");
	}
	function Bp(e, t, n, r) {
		if (e.length === 0) return -1;
		r = zp(r);
		for (var i = 0; i < e.length; i++) {
			var a = e[i];
			if (a.type === t && a.listener === n && zp(a.optionsOrUseCapture) === r) return i;
		}
		return -1;
	}
	Fp.prototype.dispatchEvent = function(e) {
		var t = p(this._fragmentFiber);
		if (t === null) return !0;
		t = v(t);
		var n = this._eventListeners;
		if (n !== null && 0 < n.length || !e.bubbles) {
			var r = t.nodeType === 9 ? t.createComment("") : document.createTextNode("");
			if (n) for (var i = 0; i < n.length; i++) {
				var a = n[i];
				r.addEventListener(a.type, a.attachedListener, Rp(a.optionsOrUseCapture));
			}
			if (t.appendChild(r), e = r.dispatchEvent(e), n) for (i = 0; i < n.length; i++) a = n[i], r.removeEventListener(a.type, a.attachedListener, Rp(a.optionsOrUseCapture));
			return t.removeChild(r), e;
		}
		return t.dispatchEvent(e);
	}, Fp.prototype.focus = function(e) {
		f(this._fragmentFiber.child, !0, Vp, e, void 0, void 0);
	};
	function Vp(e, t) {
		return e.tag !== 6 && (e = v(e), pm(e, t));
	}
	Fp.prototype.focusLast = function(e) {
		var t = [];
		f(this._fragmentFiber.child, !0, Hp, t, void 0, void 0);
		for (var n = t.length - 1; 0 <= n && !Vp(t[n], e); n--);
	};
	function Hp(e, t) {
		return t.push(e), !1;
	}
	Fp.prototype.blur = function() {
		var e = p(this._fragmentFiber);
		e !== null && (e = v(e), e = lp(e).activeElement, e !== null && f(this._fragmentFiber.child, !1, Up, e, void 0, void 0));
	};
	function Up(e, t) {
		return e.tag !== 6 && (e = v(e), e === t || e.contains(t) ? (t.blur(), !0) : !1);
	}
	Fp.prototype.observeUsing = function(e) {
		this._observers === null && (this._observers = /* @__PURE__ */ new Set()), this._observers.add(e), f(this._fragmentFiber.child, !1, Wp, e, void 0, void 0);
	};
	function Wp(e, t) {
		return e.tag !== 6 && (e = v(e), t.observe(e), !1);
	}
	Fp.prototype.unobserveUsing = function(e) {
		var t = this._observers;
		if (t !== null && t.has(e)) {
			t.delete(e), f(this._fragmentFiber.child, !1, Gp, e, void 0, void 0);
			for (var n = t = 0; n < Kp.length; n++) {
				var r = Kp[n];
				r.fragmentInstance === this && r.observer === e ? e.unobserve(r.instance) : Kp[t++] = r;
			}
			Kp.length = t;
		}
	};
	function Gp(e, t) {
		return e.tag !== 6 && (e = v(e), t.unobserve(e), !1);
	}
	var Kp = [], qp = !1;
	function Jp(e, t, n) {
		Kp.push({
			fragmentInstance: e,
			observer: t,
			instance: n
		}), qp || (qp = !0, mm(function() {
			qp = !1;
			var e = Kp;
			Kp = [];
			for (var t = 0; t < e.length; t++) {
				var n = e[t];
				n.observer.unobserve(n.instance);
			}
		}));
	}
	Fp.prototype.getClientRects = function() {
		var e = [];
		return f(this._fragmentFiber.child, !1, Yp, e, void 0, void 0), e;
	};
	function Yp(e, t) {
		if (e.tag === 6) {
			e = e.stateNode;
			var n = e.ownerDocument.createRange();
			n.selectNodeContents(e), t.push.apply(t, n.getClientRects());
		} else e = v(e), t.push.apply(t, e.getClientRects());
		return !1;
	}
	Fp.prototype.getRootNode = function(e) {
		var t = p(this._fragmentFiber);
		return t === null ? this : v(t).getRootNode(e);
	}, Fp.prototype.compareDocumentPosition = function(e) {
		var t = p(this._fragmentFiber);
		if (t === null) return Node.DOCUMENT_POSITION_DISCONNECTED;
		var n = [];
		f(this._fragmentFiber.child, !1, Hp, n, void 0, void 0);
		var r = v(t);
		if (n.length === 0) {
			if (n = r, m(this._fragmentFiber)) {
				a: {
					for (t = this._fragmentFiber.return; t !== null;) {
						if (t.tag === 4) {
							t = t.stateNode.containerInfo;
							break a;
						}
						if (t.tag === 3 || t.tag === 5 || t.tag === 27) break;
						t = t.return;
					}
					t = null;
				}
				t != null && (n = t);
			}
			t = this._fragmentFiber;
			var i = r = n.compareDocumentPosition(e);
			return n === e ? i = Node.DOCUMENT_POSITION_CONTAINS : r & Node.DOCUMENT_POSITION_CONTAINED_BY && (n = h(t)[1], n === null ? i = Node.DOCUMENT_POSITION_PRECEDING : (e = v(n).compareDocumentPosition(e), i = e === 0 || e & Node.DOCUMENT_POSITION_FOLLOWING ? Node.DOCUMENT_POSITION_FOLLOWING : Node.DOCUMENT_POSITION_PRECEDING)), i |= Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC;
		}
		t = v(n[0]), i = v(n[n.length - 1]);
		var a = m(this._fragmentFiber) ? t.parentElement : r;
		if (a == null) return Node.DOCUMENT_POSITION_DISCONNECTED;
		r = a.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_CONTAINED_BY, a = a.compareDocumentPosition(i) & Node.DOCUMENT_POSITION_CONTAINED_BY;
		var o = t.compareDocumentPosition(e), s = i.compareDocumentPosition(e), c = o & Node.DOCUMENT_POSITION_CONTAINED_BY || s & Node.DOCUMENT_POSITION_CONTAINED_BY;
		return s = r && a && o & Node.DOCUMENT_POSITION_FOLLOWING && s & Node.DOCUMENT_POSITION_PRECEDING, t = r && t === e || a && i === e || c || s ? Node.DOCUMENT_POSITION_CONTAINED_BY : !r && t === e || !a && i === e ? Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC : o, t & Node.DOCUMENT_POSITION_DISCONNECTED || t & Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC || Xp(t, this._fragmentFiber, n[0], n[n.length - 1], e) ? t : Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC;
	};
	function Xp(e, t, n, r, i) {
		var a = At(i);
		if (e & Node.DOCUMENT_POSITION_CONTAINED_BY) {
			if (n = !!a) a: {
				for (; a !== null;) {
					if (a.tag === 7 && (a === t || a.alternate === t)) {
						n = !0;
						break a;
					}
					a = a.return;
				}
				n = !1;
			}
			return n;
		}
		if (e & Node.DOCUMENT_POSITION_CONTAINS) {
			if (a === null) return a = i.ownerDocument, i === a || i === a.documentElement || i === a.body;
			a: {
				for (a = t, t = p(t); a !== null;) {
					if (!(a.tag !== 5 && a.tag !== 3 && a.tag !== 27 || a !== t && a.alternate !== t)) {
						a = !0;
						break a;
					}
					a = a.return;
				}
				a = !1;
			}
			return a;
		}
		return e & Node.DOCUMENT_POSITION_PRECEDING ? ((t = !!a) && !(t = a === n) && (t = w(n, a, C), t === null ? t = !1 : (f(t, !0, x, a, n), a = y, y = null, t = a !== null)), t) : e & Node.DOCUMENT_POSITION_FOLLOWING ? ((t = !!a) && !(t = a === r) && (t = w(r, a, C), t === null ? t = !1 : (f(t, !0, S, a, r), a = y, b = y = null, t = a !== null)), t) : !1;
	}
	function Zp(e, t) {
		var n = e.ownerDocument.createRange();
		n.selectNodeContents(e), e = n.getBoundingClientRect(), window.scrollTo(window.scrollX + e.left, t ? window.scrollY + e.top : window.scrollY + e.bottom - window.innerHeight);
	}
	Fp.prototype.scrollIntoView = function(e) {
		if (typeof e == "object") throw Error(i(566));
		var t = [];
		f(this._fragmentFiber.child, !1, Hp, t, void 0, void 0);
		var n = !1 !== e;
		if (t.length === 0) {
			var r = h(this._fragmentFiber);
			if (r = n ? r[1] || r[0] || p(this._fragmentFiber) : r[0] || r[1], r === null) return;
			if (r.tag === 6) {
				e = v(r), Zp(e, n);
				return;
			}
			if (r = v(r), r.nodeType !== 9) {
				if (r.nodeType === 11) {
					n = "host" in r ? r.host : null, n !== null && n.scrollIntoView(e);
					return;
				}
				r.scrollIntoView(e);
			}
		}
		for (r = n ? t.length - 1 : 0; r !== (n ? -1 : t.length);) {
			var a = t[r];
			a.tag === 6 ? (a = v(a), Zp(a, n)) : v(a).scrollIntoView(e), r += n ? -1 : 1;
		}
	};
	function Qp(e, t) {
		return e = v(e), $p(e, t), !1;
	}
	function $p(e, t) {
		e.reactFragments ??= /* @__PURE__ */ new Set(), e.reactFragments.add(t);
	}
	function em(e, t) {
		var n = t._eventListeners;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var i = n[r];
			e.addEventListener(i.type, i.attachedListener, Rp(i.optionsOrUseCapture));
		}
		e.nodeType !== 3 && (n = t._observers, n !== null && n.forEach(function(n) {
			for (var r = 0, i = 0; i < Kp.length; i++) {
				var a = Kp[i];
				(a.fragmentInstance !== t || a.observer !== n || a.instance !== e) && (Kp[r++] = a);
			}
			Kp.length = r, n.observe(e);
		}), $p(e, t));
	}
	function tm(e, t) {
		var n = t._eventListeners;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var i = n[r];
			e.removeEventListener(i.type, i.attachedListener, Rp(i.optionsOrUseCapture));
		}
		e.nodeType !== 3 && (n = t._observers, n !== null && n.forEach(function(n) {
			typeof n.rootMargin == "string" ? Jp(t, n, e) : n.unobserve(e);
		}), e.reactFragments != null && e.reactFragments.delete(t));
	}
	function nm(e) {
		var t = e.firstChild;
		for (t && t.nodeType === 10 && (t = t.nextSibling); t;) {
			var n = t;
			switch (t = t.nextSibling, n.nodeName) {
				case "HTML":
				case "HEAD":
				case "BODY":
					nm(n), kt(n);
					continue;
				case "SCRIPT":
				case "STYLE": continue;
				case "LINK": if (n.rel.toLowerCase() === "stylesheet") continue;
			}
			e.removeChild(n);
		}
	}
	function rm(e, t, n, r) {
		for (; e.nodeType === 1;) {
			var i = n;
			if (e.nodeName.toLowerCase() !== t.toLowerCase()) {
				if (!r && (e.nodeName !== "INPUT" || e.type !== "hidden")) break;
			} else if (!r) {
				if (t === "input" && e.type === "hidden") {
					var a = i.name == null ? null : "" + i.name;
					if (i.type === "hidden" && e.getAttribute("name") === a) return e;
				} else return e;
			} else if (!e[Dt]) switch (t) {
				case "meta":
					if (!e.hasAttribute("itemprop")) break;
					return e;
				case "link":
					if (a = e.getAttribute("rel"), a === "stylesheet" && e.hasAttribute("data-precedence") || a !== i.rel || e.getAttribute("href") !== (i.href == null || i.href === "" ? null : i.href) || e.getAttribute("crossorigin") !== (i.crossOrigin == null ? null : i.crossOrigin) || e.getAttribute("title") !== (i.title == null ? null : i.title)) break;
					return e;
				case "style":
					if (e.hasAttribute("data-precedence")) break;
					return e;
				case "script":
					if (a = e.getAttribute("src"), (a !== (i.src == null ? null : i.src) || e.getAttribute("type") !== (i.type == null ? null : i.type) || e.getAttribute("crossorigin") !== (i.crossOrigin == null ? null : i.crossOrigin)) && a && e.hasAttribute("async") && !e.hasAttribute("itemprop")) break;
					return e;
				default: return e;
			}
			if (e = lm(e.nextSibling), e === null) break;
		}
		return null;
	}
	function im(e, t, n) {
		if (t === "") return null;
		for (; e.nodeType !== 3;) if ((e.nodeType !== 1 || e.nodeName !== "INPUT" || e.type !== "hidden") && !n || (e = lm(e.nextSibling), e === null)) return null;
		return e;
	}
	function am(e, t) {
		for (; e.nodeType !== 8;) if ((e.nodeType !== 1 || e.nodeName !== "INPUT" || e.type !== "hidden") && !t || (e = lm(e.nextSibling), e === null)) return null;
		return e;
	}
	function om(e) {
		return e.data === "$?" || e.data === "$~";
	}
	function sm(e) {
		return e.data === "$!" || e.data === "$?" && e.ownerDocument.readyState !== "loading";
	}
	function cm(e, t) {
		var n = e.ownerDocument;
		if (e.data === "$~") e._reactRetry = t;
		else if (e.data !== "$?" || n.readyState !== "loading") t();
		else {
			var r = function() {
				t(), n.removeEventListener("DOMContentLoaded", r);
			};
			n.addEventListener("DOMContentLoaded", r), e._reactRetry = r;
		}
	}
	function lm(e) {
		for (; e != null; e = e.nextSibling) {
			var t = e.nodeType;
			if (t === 1 || t === 3) break;
			if (t === 8) {
				if (t = e.data, t === "$" || t === "$!" || t === "$?" || t === "$~" || t === "&" || t === "F!" || t === "F") break;
				if (t === "/$" || t === "/&") return null;
			}
		}
		return e;
	}
	var um = null;
	function dm(e) {
		e = e.nextSibling;
		for (var t = 0; e;) {
			if (e.nodeType === 8) {
				var n = e.data;
				if (n === "/$" || n === "/&") {
					if (t === 0) return lm(e.nextSibling);
					t--;
				} else n !== "$" && n !== "$!" && n !== "$?" && n !== "$~" && n !== "&" || t++;
			}
			e = e.nextSibling;
		}
		return null;
	}
	function fm(e) {
		e = e.previousSibling;
		for (var t = 0; e;) {
			if (e.nodeType === 8) {
				var n = e.data;
				if (n === "$" || n === "$!" || n === "$?" || n === "$~" || n === "&") {
					if (t === 0) return e;
					t--;
				} else n !== "/$" && n !== "/&" || t++;
			}
			e = e.previousSibling;
		}
		return null;
	}
	function pm(e, t) {
		function n() {
			r = !0;
		}
		if (e.ownerDocument.activeElement === e) return !0;
		var r = !1;
		try {
			e.ownerDocument.addEventListener("focus", n, !0), (e.focus || HTMLElement.prototype.focus).call(e, t);
		} finally {
			e.ownerDocument.removeEventListener("focus", n, !0);
		}
		return r;
	}
	function mm(e) {
		yp(function() {
			yp(function(t) {
				return e(t);
			});
		});
	}
	function hm(e, t, n) {
		switch (t = lp(n), e) {
			case "html":
				if (e = t.documentElement, !e) throw Error(i(452));
				return e;
			case "head":
				if (e = t.head, !e) throw Error(i(453));
				return e;
			case "body":
				if (e = t.body, !e) throw Error(i(454));
				return e;
			default: throw Error(i(451));
		}
	}
	function gm(e, t, n) {
		for (var r in n) {
			var i = n[r];
			n.hasOwnProperty(r) && i != null && ep(e, t, r, null, rp, i);
		}
		n.dangerouslySetInnerHTML != null && (e.textContent = ""), e.onclick === pn && (e.onclick = null), kt(e);
	}
	function _m(e) {
		for (var t = e.attributes; t.length;) e.removeAttributeNode(t[0]);
		kt(e);
	}
	var vm = /* @__PURE__ */ new Map(), ym = /* @__PURE__ */ new Set();
	function bm(e) {
		if (typeof e.getRootNode == "function") {
			var t = e.getRootNode();
			if (t.nodeType === 9 || t.nodeType === 11) return t;
		}
		return e.nodeType === 9 ? e : e.ownerDocument;
	}
	var xm = L.d;
	L.d = {
		f: Sm,
		r: Cm,
		D: Em,
		C: Dm,
		L: Om,
		m: km,
		X: jm,
		S: Am,
		M: Mm
	};
	function Sm() {
		var e = xm.f(), t = Ld();
		return e || t;
	}
	function Cm(e) {
		var t = z(e);
		t !== null && t.tag === 5 && t.type === "form" ? $s(t) : xm.r(e);
	}
	var wm = typeof document > "u" ? null : document;
	function Tm(e, t, n) {
		var r = wm;
		if (r && typeof t == "string" && t) {
			var i = Zt(t);
			i = "link[rel=\"" + e + "\"][href=\"" + i + "\"]", typeof n == "string" && (i += "[crossorigin=\"" + n + "\"]"), ym.has(i) || (ym.add(i), e = {
				rel: e,
				crossOrigin: n,
				href: t
			}, r.querySelector(i) === null && (t = r.createElement("link"), np(t, "link", e), Mt(t), r.head.appendChild(t)));
		}
	}
	function Em(e) {
		xm.D(e), Tm("dns-prefetch", e, null);
	}
	function Dm(e, t) {
		xm.C(e, t), Tm("preconnect", e, t);
	}
	function Om(e, t, n) {
		xm.L(e, t, n);
		var r = wm;
		if (r && e && t) {
			var i = "link[rel=\"preload\"][as=\"" + Zt(t) + "\"]";
			t === "image" && n && n.imageSrcSet ? (i += "[imagesrcset=\"" + Zt(n.imageSrcSet) + "\"]", typeof n.imageSizes == "string" && (i += "[imagesizes=\"" + Zt(n.imageSizes) + "\"]")) : i += "[href=\"" + Zt(e) + "\"]";
			var a = i;
			switch (t) {
				case "style":
					a = Pm(e);
					break;
				case "script": a = Rm(e);
			}
			if (!(vm.has(a) || (e = T({
				rel: "preload",
				href: t === "image" && n && n.imageSrcSet ? void 0 : e,
				as: t
			}, n), vm.set(a, e), r.querySelector(i) !== null || t === "style" && r.querySelector(Fm(a)) || t === "script" && r.querySelector(zm(a))))) {
				var o = r.createElement("link");
				np(o, "link", e), t === "style" && (o[Ot] = !0, o.onload = o.onerror = function() {
					Nt(o);
				}), Mt(o), r.head.appendChild(o);
			}
		}
	}
	function km(e, t) {
		xm.m(e, t);
		var n = wm;
		if (n && e) {
			var r = t && typeof t.as == "string" ? t.as : "script", i = "link[rel=\"modulepreload\"][as=\"" + Zt(r) + "\"][href=\"" + Zt(e) + "\"]", a = i;
			switch (r) {
				case "audioworklet":
				case "paintworklet":
				case "serviceworker":
				case "sharedworker":
				case "worker":
				case "script": a = Rm(e);
			}
			if (!vm.has(a) && (e = T({
				rel: "modulepreload",
				href: e
			}, t), vm.set(a, e), n.querySelector(i) === null)) {
				switch (r) {
					case "audioworklet":
					case "paintworklet":
					case "serviceworker":
					case "sharedworker":
					case "worker":
					case "script": if (n.querySelector(zm(a))) return;
				}
				r = n.createElement("link"), np(r, "link", e), Mt(r), n.head.appendChild(r);
			}
		}
	}
	function Am(e, t, n) {
		xm.S(e, t, n);
		var r = wm;
		if (r && e) {
			var i = B(r).hoistableStyles, a = Pm(e);
			t ||= "default";
			var o = i.get(a);
			if (!o) {
				var s = {
					loading: 0,
					preload: null
				};
				if (o = r.querySelector(Fm(a))) s.loading = 5;
				else {
					e = T({
						rel: "stylesheet",
						href: e,
						"data-precedence": t
					}, n), (n = vm.get(a)) && Hm(e, n);
					var c = o = r.createElement("link");
					Mt(c), np(c, "link", e), c._p = new Promise(function(e, t) {
						c.onload = e, c.onerror = t;
					}), c.addEventListener("load", function() {
						s.loading |= 1;
					}), c.addEventListener("error", function() {
						s.loading |= 2;
					}), s.loading |= 4, Vm(o, t, r);
				}
				o = {
					type: "stylesheet",
					instance: o,
					count: 1,
					state: s
				}, i.set(a, o);
			}
		}
	}
	function jm(e, t) {
		xm.X(e, t);
		var n = wm;
		if (n && e) {
			var r = B(n).hoistableScripts, i = Rm(e), a = r.get(i);
			a || (a = n.querySelector(zm(i)), a || (e = T({
				src: e,
				async: !0
			}, t), (t = vm.get(i)) && Um(e, t), a = n.createElement("script"), Mt(a), np(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function Mm(e, t) {
		xm.M(e, t);
		var n = wm;
		if (n && e) {
			var r = B(n).hoistableScripts, i = Rm(e), a = r.get(i);
			a || (a = n.querySelector(zm(i)), a || (e = T({
				src: e,
				async: !0,
				type: "module"
			}, t), (t = vm.get(i)) && Um(e, t), a = n.createElement("script"), Mt(a), np(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function Nm(e, t, n, r) {
		var a = (a = xe.current) ? bm(a) : null;
		if (!a) throw Error(i(446));
		switch (e) {
			case "meta":
			case "title": return null;
			case "style": return typeof n.precedence == "string" && typeof n.href == "string" ? (n = Pm(n.href), t = B(a).hoistableStyles, r = t.get(n), r || (r = {
				type: "style",
				instance: null,
				count: 0,
				state: null
			}, t.set(n, r)), r) : {
				type: "void",
				instance: null,
				count: 0,
				state: null
			};
			case "link":
				if (n.rel === "stylesheet" && typeof n.href == "string" && typeof n.precedence == "string") {
					e = Pm(n.href);
					var o = B(a).hoistableStyles, s = o.get(e);
					if (s || (a = a.ownerDocument || a, s = {
						type: "stylesheet",
						instance: null,
						count: 0,
						state: {
							loading: 0,
							preload: null
						}
					}, o.set(e, s), (o = a.querySelector(Fm(e))) ? o._p || (s.instance = o, s.state.loading = 5) : (o = vm.get(e), o || (o = {
						rel: "preload",
						as: "style",
						href: n.href,
						crossOrigin: n.crossOrigin,
						integrity: n.integrity,
						media: n.media,
						hrefLang: n.hrefLang,
						referrerPolicy: n.referrerPolicy
					}, vm.set(e, o)), Lm(a, e, o, s.state))), t && r === null) throw Error(i(528, ""));
					return s;
				}
				if (t && r !== null) throw Error(i(529, ""));
				return null;
			case "script": return t = n.async, n = n.src, typeof n == "string" && t && typeof t != "function" && typeof t != "symbol" ? (n = Rm(n), t = B(a).hoistableScripts, r = t.get(n), r || (r = {
				type: "script",
				instance: null,
				count: 0,
				state: null
			}, t.set(n, r)), r) : {
				type: "void",
				instance: null,
				count: 0,
				state: null
			};
			default: throw Error(i(444, e));
		}
	}
	function Pm(e) {
		return "href=\"" + Zt(e) + "\"";
	}
	function Fm(e) {
		return "link[rel=\"stylesheet\"][" + e + "]";
	}
	function Im(e) {
		return T({}, e, {
			"data-precedence": e.precedence,
			precedence: null
		});
	}
	function Lm(e, t, n, r) {
		if (t = e.querySelector("link[rel=\"preload\"][as=\"style\"][" + t + "]")) {
			if (!0 !== t[Ot]) {
				r.loading = 1;
				return;
			}
		} else t = e.createElement("link"), t[Ot] = !0, t.onload = t.onerror = Nt.bind(null, t), np(t, "link", n), Mt(t), e.head.appendChild(t);
		r.preload = t, t.addEventListener("load", function() {
			return r.loading |= 1;
		}), t.addEventListener("error", function() {
			return r.loading |= 2;
		});
	}
	function Rm(e) {
		return "[src=\"" + Zt(e) + "\"]";
	}
	function zm(e) {
		return "script[async]" + e;
	}
	function Bm(e, t, n) {
		if (t.count++, t.instance === null) switch (t.type) {
			case "style":
				var r = e.querySelector("style[data-href~=\"" + Zt(n.href) + "\"]");
				if (r) return t.instance = r, Mt(r), r;
				var a = T({}, n, {
					"data-href": n.href,
					"data-precedence": n.precedence,
					href: null,
					precedence: null
				});
				return r = (e.ownerDocument || e).createElement("style"), Mt(r), np(r, "style", a), Vm(r, n.precedence, e), t.instance = r;
			case "stylesheet":
				a = Pm(n.href);
				var o = e.querySelector(Fm(a));
				if (o) return t.state.loading |= 4, t.instance = o, Mt(o), o;
				r = Im(n), (a = vm.get(a)) && Hm(r, a), o = (e.ownerDocument || e).createElement("link"), Mt(o);
				var s = o;
				return s._p = new Promise(function(e, t) {
					s.onload = e, s.onerror = t;
				}), np(o, "link", r), t.state.loading |= 4, Vm(o, n.precedence, e), t.instance = o;
			case "script": return o = Rm(n.src), (a = e.querySelector(zm(o))) ? (t.instance = a, Mt(a), a) : (r = n, (a = vm.get(o)) && (r = T({}, n), Um(r, a)), e = e.ownerDocument || e, a = e.createElement("script"), Mt(a), np(a, "link", r), e.head.appendChild(a), t.instance = a);
			case "void": return null;
			default: throw Error(i(443, t.type));
		}
		else t.type === "stylesheet" && !(t.state.loading & 4) && (r = t.instance, t.state.loading |= 4, Vm(r, n.precedence, e));
		return t.instance;
	}
	function Vm(e, t, n) {
		for (var r = n.querySelectorAll("link[rel=\"stylesheet\"][data-precedence],style[data-precedence]"), i = r.length ? r[r.length - 1] : null, a = i, o = 0; o < r.length; o++) {
			var s = r[o];
			if (s.dataset.precedence === t) a = s;
			else if (a !== i) break;
		}
		a ? a.parentNode.insertBefore(e, a.nextSibling) : (t = n.nodeType === 9 ? n.head : n, t.insertBefore(e, t.firstChild));
	}
	function Hm(e, t) {
		e.crossOrigin ??= t.crossOrigin, e.referrerPolicy ??= t.referrerPolicy, e.title ??= t.title;
	}
	function Um(e, t) {
		e.crossOrigin ??= t.crossOrigin, e.referrerPolicy ??= t.referrerPolicy, e.integrity ??= t.integrity;
	}
	var Wm = null;
	function Gm(e, t, n) {
		if (Wm === null) {
			var r = /* @__PURE__ */ new Map(), i = Wm = /* @__PURE__ */ new Map();
			i.set(n, r);
		} else i = Wm, r = i.get(n), r || (r = /* @__PURE__ */ new Map(), i.set(n, r));
		if (r.has(e)) return r;
		for (r.set(e, null), n = n.getElementsByTagName(e), i = 0; i < n.length; i++) {
			var a = n[i];
			if (!(a[Dt] || a[xt] || e === "link" && a.getAttribute("rel") === "stylesheet") && a.namespaceURI !== "http://www.w3.org/2000/svg") {
				var o = a.getAttribute(t) || "";
				o = e + o;
				var s = r.get(o);
				s ? s.push(a) : r.set(o, [a]);
			}
		}
		return r;
	}
	function Km(e, t, n) {
		e = e.ownerDocument || e, e.head.insertBefore(n, t === "title" ? e.querySelector("head > title") : null);
	}
	function qm(e, t, n) {
		if (n === 1 || t.itemProp != null) return !1;
		switch (e) {
			case "meta":
			case "title": return !0;
			case "style":
				if (typeof t.precedence != "string" || typeof t.href != "string" || t.href === "") break;
				return !0;
			case "link":
				if (typeof t.rel != "string" || typeof t.href != "string" || t.href === "" || t.onLoad || t.onError) break;
				switch (t.rel) {
					case "stylesheet": return e = t.disabled, typeof t.precedence == "string" && e == null;
					default: return !0;
				}
			case "script": if (t.async && typeof t.async != "function" && typeof t.async != "symbol" && !t.onLoad && !t.onError && t.src && typeof t.src == "string") return !0;
		}
		return !1;
	}
	function Jm(e, t) {
		return e === "img" && t.src != null && t.src !== "" && t.onLoad == null && t.loading !== "lazy";
	}
	function Ym(e) {
		return !(e.type === "stylesheet" && !(e.state.loading & 3));
	}
	function Xm(e) {
		return (e.width || 100) * (e.height || 100) * (typeof devicePixelRatio == "number" ? devicePixelRatio : 1) * .25;
	}
	function Zm(e, t) {
		typeof t.decode == "function" && (e.imgCount++, t.complete || (e.imgBytes += Xm(t), e.suspenseyImages.push(t)), e = rh.bind(e), t.decode().then(e, e));
	}
	function Qm(e, t, n, r) {
		if (n.type === "stylesheet" && (typeof r.media != "string" || !1 !== matchMedia(r.media).matches) && !(n.state.loading & 4)) {
			if (n.instance === null) {
				var i = Pm(r.href), a = t.querySelector(Fm(i));
				if (a) {
					t = a._p, typeof t == "object" && t && typeof t.then == "function" && (e.count++, e = nh.bind(e), t.then(e, e)), n.state.loading |= 4, n.instance = a, Mt(a);
					return;
				}
				a = t.ownerDocument || t, r = Im(r), (i = vm.get(i)) && Hm(r, i), a = a.createElement("link"), Mt(a);
				var o = a;
				o._p = new Promise(function(e, t) {
					o.onload = e, o.onerror = t;
				}), np(a, "link", r), n.instance = a;
			}
			e.stylesheets === null && (e.stylesheets = /* @__PURE__ */ new Map()), e.stylesheets.set(n, t), (t = n.state.preload) && !(n.state.loading & 3) && (e.count++, n = nh.bind(e), t.addEventListener("load", n), t.addEventListener("error", n));
		}
	}
	var $m = 0;
	function eh(e, t) {
		return e.stylesheets && e.count === 0 && ah(e, e.stylesheets), 0 < e.count || 0 < e.imgCount ? function(n) {
			var r = setTimeout(function() {
				if (e.stylesheets && ah(e, e.stylesheets), e.unsuspend) {
					var t = e.unsuspend;
					e.unsuspend = null, t();
				}
			}, 6e4 + t);
			0 < e.imgBytes && $m === 0 && ($m = 62500 * op());
			var i = setTimeout(function() {
				if (e.waitingForImages = !1, e.count === 0 && (e.stylesheets && ah(e, e.stylesheets), e.unsuspend)) {
					var t = e.unsuspend;
					e.unsuspend = null, t();
				}
			}, (e.imgBytes > $m ? 50 : 800) + t);
			return e.unsuspend = n, function() {
				e.unsuspend = null, clearTimeout(r), clearTimeout(i);
			};
		} : null;
	}
	function th(e) {
		if (e.count === 0 && (e.imgCount === 0 || !e.waitingForImages)) {
			if (e.stylesheets) ah(e, e.stylesheets);
			else if (e.unsuspend) {
				var t = e.unsuspend;
				e.unsuspend = null, t();
			}
		}
	}
	function nh() {
		this.count--, th(this);
	}
	function rh() {
		this.imgCount--, th(this);
	}
	var ih = null;
	function ah(e, t) {
		e.stylesheets = null, e.unsuspend !== null && (e.count++, ih = /* @__PURE__ */ new Map(), t.forEach(oh, e), ih = null, nh.call(e));
	}
	function oh(e, t) {
		if (!(t.state.loading & 4)) {
			var n = ih.get(e);
			if (n) var r = n.get(null);
			else {
				n = /* @__PURE__ */ new Map(), ih.set(e, n);
				for (var i = e.querySelectorAll("link[data-precedence],style[data-precedence]"), a = 0; a < i.length; a++) {
					var o = i[a];
					(o.nodeName === "LINK" || o.getAttribute("media") !== "not all") && (n.set(o.dataset.precedence, o), r = o);
				}
				r && n.set(null, r);
			}
			i = t.instance, o = i.getAttribute("data-precedence"), a = n.get(o) || r, a === r && n.set(null, i), n.set(o, i), this.count++, r = nh.bind(this), i.addEventListener("load", r), i.addEventListener("error", r), a ? a.parentNode.insertBefore(i, a.nextSibling) : (e = e.nodeType === 9 ? e.head : e, e.insertBefore(i, e.firstChild)), t.state.loading |= 4;
		}
	}
	var sh = {
		$$typeof: N,
		Provider: null,
		Consumer: null,
		_currentValue: pe,
		_currentValue2: pe,
		_threadCount: 0
	};
	function ch(e, t, n, r, i, a, o, s, c) {
		this.tag = 1, this.containerInfo = e, this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.next = this.pendingContext = this.context = this.cancelPendingCommit = null, this.callbackPriority = 0, this.expirationTimes = ut(-1), this.entangledLanes = this.shellSuspendCounter = this.errorRecoveryDisabledLanes = this.expiredLanes = this.warmLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = ut(0), this.hiddenUpdates = ut(null), this.identifierPrefix = r, this.onUncaughtError = i, this.onCaughtError = a, this.onRecoverableError = o, this.pooledCache = null, this.pooledCacheLanes = 0, this.formState = c, this.transitionTypes = null, this.incompleteTransitions = /* @__PURE__ */ new Map();
	}
	function lh(e, t, n, r, i, a, o, s, c, l, u, d) {
		return e = new ch(e, t, n, o, c, l, u, d, s), t = 1, !0 === a && (t |= 24), a = Di(3, null, null, t), e.current = a, a.stateNode = e, t = Da(), t.refCount++, e.pooledCache = t, t.refCount++, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: t
		}, lo(a), e;
	}
	function uh(e) {
		return e ? (e = Ti, e) : Ti;
	}
	function dh(e, t, n, r, i, a) {
		i = uh(i), r.context === null ? r.context = i : r.pendingContext = i, r = fo(t), r.payload = { element: n }, a = a === void 0 ? null : a, a !== null && (r.callback = a), n = po(e, r, t), n !== null && (Md(n, e, t), mo(n, e, t));
	}
	function fh(e, t) {
		if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
			var n = e.retryLane;
			e.retryLane = n !== 0 && n < t ? n : t;
		}
	}
	function ph(e, t) {
		fh(e, t), (e = e.alternate) && fh(e, t);
	}
	function mh(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = Si(e, 67108864);
			t !== null && Md(t, e, 67108864), ph(e, 67108864);
		}
	}
	function hh(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = kd();
			t = gt(t);
			var n = Si(e, t);
			n !== null && Md(n, e, t), ph(e, t);
		}
	}
	var gh = !0;
	function _h(e, t, n, r) {
		var i = I.T;
		I.T = null;
		var a = L.p;
		try {
			L.p = 2, yh(e, t, n, r);
		} finally {
			L.p = a, I.T = i;
		}
	}
	function vh(e, t, n, r) {
		var i = I.T;
		I.T = null;
		var a = L.p;
		try {
			L.p = 8, yh(e, t, n, r);
		} finally {
			L.p = a, I.T = i;
		}
	}
	function yh(e, t, n, r) {
		if (gh) {
			var i = bh(r);
			if (i === null) Gf(e, t, r, xh, n), Mh(e, r);
			else if (Ph(i, e, t, n, r)) r.stopPropagation();
			else if (Mh(e, r), t & 4 && -1 < jh.indexOf(e)) {
				for (; i !== null;) {
					var a = z(i);
					if (a !== null) switch (a.tag) {
						case 3:
							if (a = a.stateNode, a.current.memoizedState.isDehydrated) {
								var o = it(a.pendingLanes);
								if (o !== 0) {
									var s = a;
									for (s.pendingLanes |= 2, s.entangledLanes |= 2; o;) {
										var c = 1 << 31 - Ze(o);
										s.entanglements[1] |= c, o &= ~c;
									}
									Tf(a), !($u & 6) && (hd = ze() + 500, Ef(0, !1));
								}
							}
							break;
						case 31:
						case 13: s = Si(a, 2), s !== null && Md(s, a, 2), Ld(), ph(a, 2);
					}
					if (a = bh(r), a === null && Gf(e, t, r, xh, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else Gf(e, t, r, null, n);
		}
	}
	function bh(e) {
		return e = hn(e), Sh(e);
	}
	var xh = null;
	function Sh(e) {
		if (xh = null, e = At(e), e !== null) {
			var t = o(e);
			if (t === null) e = null;
			else {
				var n = t.tag;
				if (n === 13) {
					if (e = s(t), e !== null) return e;
					e = null;
				} else if (n === 31) {
					if (e = c(t), e !== null) return e;
					e = null;
				} else if (n === 3) {
					if (t.stateNode.current.memoizedState.isDehydrated) return t.tag === 3 ? t.stateNode.containerInfo : null;
					e = null;
				} else t !== e && (e = null);
			}
		}
		return xh = e, null;
	}
	function Ch(e) {
		switch (e) {
			case "beforetoggle":
			case "cancel":
			case "click":
			case "close":
			case "contextmenu":
			case "copy":
			case "cut":
			case "auxclick":
			case "dblclick":
			case "dragend":
			case "dragstart":
			case "drop":
			case "focusin":
			case "focusout":
			case "input":
			case "invalid":
			case "keydown":
			case "keypress":
			case "keyup":
			case "mousedown":
			case "mouseup":
			case "paste":
			case "pause":
			case "play":
			case "pointercancel":
			case "pointerdown":
			case "pointerup":
			case "ratechange":
			case "reset":
			case "seeked":
			case "submit":
			case "toggle":
			case "touchcancel":
			case "touchend":
			case "touchstart":
			case "volumechange":
			case "change":
			case "selectionchange":
			case "textInput":
			case "compositionstart":
			case "compositionend":
			case "compositionupdate":
			case "beforeblur":
			case "afterblur":
			case "beforeinput":
			case "blur":
			case "fullscreenchange":
			case "fullscreenerror":
			case "focus":
			case "hashchange":
			case "popstate":
			case "select":
			case "selectstart": return 2;
			case "drag":
			case "dragenter":
			case "dragexit":
			case "dragleave":
			case "dragover":
			case "mousemove":
			case "mouseout":
			case "mouseover":
			case "pointermove":
			case "pointerout":
			case "pointerover":
			case "resize":
			case "scroll":
			case "touchmove":
			case "wheel":
			case "mouseenter":
			case "mouseleave":
			case "pointerenter":
			case "pointerleave": return 8;
			case "message": switch (Be()) {
				case Ve: return 2;
				case He: return 8;
				case Ue:
				case We: return 32;
				case Ge: return 268435456;
				default: return 32;
			}
			default: return 32;
		}
	}
	var wh = !1, Th = null, Eh = null, Dh = null, Oh = /* @__PURE__ */ new Map(), kh = /* @__PURE__ */ new Map(), Ah = [], jh = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset".split(" ");
	function Mh(e, t) {
		switch (e) {
			case "focusin":
			case "focusout":
				Th = null;
				break;
			case "dragenter":
			case "dragleave":
				Eh = null;
				break;
			case "mouseover":
			case "mouseout":
				Dh = null;
				break;
			case "pointerover":
			case "pointerout":
				Oh.delete(t.pointerId);
				break;
			case "gotpointercapture":
			case "lostpointercapture": kh.delete(t.pointerId);
		}
	}
	function Nh(e, t, n, r, i, a) {
		return e === null || e.nativeEvent !== a ? (e = {
			blockedOn: t,
			domEventName: n,
			eventSystemFlags: r,
			nativeEvent: a,
			targetContainers: [i]
		}, t !== null && (t = z(t), t !== null && mh(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
	}
	function Ph(e, t, n, r, i) {
		switch (t) {
			case "focusin": return Th = Nh(Th, e, t, n, r, i), !0;
			case "dragenter": return Eh = Nh(Eh, e, t, n, r, i), !0;
			case "mouseover": return Dh = Nh(Dh, e, t, n, r, i), !0;
			case "pointerover":
				var a = i.pointerId;
				return Oh.set(a, Nh(Oh.get(a) || null, e, t, n, r, i)), !0;
			case "gotpointercapture": return a = i.pointerId, kh.set(a, Nh(kh.get(a) || null, e, t, n, r, i)), !0;
		}
		return !1;
	}
	function Fh(e) {
		var t = At(e.target);
		if (t !== null) {
			var n = o(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = s(n), t !== null) {
						e.blockedOn = t, yt(e.priority, function() {
							hh(n);
						});
						return;
					}
				} else if (t === 31) {
					if (t = c(n), t !== null) {
						e.blockedOn = t, yt(e.priority, function() {
							hh(n);
						});
						return;
					}
				} else if (t === 3 && n.stateNode.current.memoizedState.isDehydrated) {
					e.blockedOn = n.tag === 3 ? n.stateNode.containerInfo : null;
					return;
				}
			}
		}
		e.blockedOn = null;
	}
	function Ih(e) {
		if (e.blockedOn !== null) return !1;
		for (var t = e.targetContainers; 0 < t.length;) {
			var n = bh(e.nativeEvent);
			if (n === null) {
				n = e.nativeEvent;
				var r = new n.constructor(n.type, n);
				mn = r, n.target.dispatchEvent(r), mn = null;
			} else return t = z(n), t !== null && mh(t), e.blockedOn = n, !1;
			t.shift();
		}
		return !0;
	}
	function Lh(e, t, n) {
		Ih(e) && n.delete(t);
	}
	function Rh() {
		wh = !1, Th !== null && Ih(Th) && (Th = null), Eh !== null && Ih(Eh) && (Eh = null), Dh !== null && Ih(Dh) && (Dh = null), Oh.forEach(Lh), kh.forEach(Lh);
	}
	function zh(e, n) {
		e.blockedOn === n && (e.blockedOn = null, wh || (wh = !0, t.unstable_scheduleCallback(t.unstable_NormalPriority, Rh)));
	}
	var Bh = null;
	function Vh(e) {
		Bh !== e && (Bh = e, t.unstable_scheduleCallback(t.unstable_NormalPriority, function() {
			Bh === e && (Bh = null);
			for (var t = 0; t < e.length; t += 3) {
				var n = e[t], r = e[t + 1], i = e[t + 2];
				if (typeof r != "function") {
					if (Sh(r || n) === null) continue;
					break;
				}
				var a = z(n);
				a !== null && (e.splice(t, 3), t -= 3, Zs(a, {
					pending: !0,
					data: i,
					method: n.method,
					action: r
				}, r, i));
			}
		}));
	}
	function Hh(e) {
		function t(t) {
			return zh(t, e);
		}
		Th !== null && zh(Th, e), Eh !== null && zh(Eh, e), Dh !== null && zh(Dh, e), Oh.forEach(t), kh.forEach(t);
		for (var n = 0; n < Ah.length; n++) {
			var r = Ah[n];
			r.blockedOn === e && (r.blockedOn = null);
		}
		for (; 0 < Ah.length && (n = Ah[0], n.blockedOn === null);) Fh(n), n.blockedOn === null && Ah.shift();
		if (n = (e.ownerDocument || e).$$reactFormReplay, n != null) for (r = 0; r < n.length; r += 3) {
			var i = n[r], a = n[r + 1], o = i[R] || null;
			if (typeof a == "function") o || Vh(n);
			else if (o) {
				var s = null;
				if (a && a.hasAttribute("formAction")) {
					if (i = a, o = a[R] || null) s = o.formAction;
					else if (Sh(i) !== null) continue;
				} else s = o.action;
				typeof s == "function" ? n[r + 1] = s : (n.splice(r, 3), r -= 3), Vh(n);
			}
		}
	}
	function Uh() {
		function e(e) {
			e.canIntercept && e.info === "react-transition" && e.intercept({
				handler: function() {
					return new Promise(function(e) {
						return i = e;
					});
				},
				focusReset: "manual",
				scroll: "manual"
			});
		}
		function t() {
			i !== null && (i(), i = null), r || setTimeout(n, 20);
		}
		function n() {
			if (!r && !navigation.transition) {
				var e = navigation.currentEntry;
				e && e.url != null && navigation.navigate(e.url, {
					state: e.getState(),
					info: "react-transition",
					history: "replace"
				});
			}
		}
		if (typeof navigation == "object") {
			var r = !1, i = null;
			return navigation.addEventListener("navigate", e), navigation.addEventListener("navigatesuccess", t), navigation.addEventListener("navigateerror", t), setTimeout(n, 100), function() {
				r = !0, navigation.removeEventListener("navigate", e), navigation.removeEventListener("navigatesuccess", t), navigation.removeEventListener("navigateerror", t), i !== null && (i(), i = null);
			};
		}
	}
	function Wh(e) {
		this._internalRoot = e;
	}
	Gh.prototype.render = Wh.prototype.render = function(e) {
		var t = this._internalRoot;
		if (t === null) throw Error(i(409));
		var n = t.current;
		dh(n, kd(), e, t, null, null);
	}, Gh.prototype.unmount = Wh.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			dh(e.current, 2, null, e, null, null), Ld(), t[St] = null;
		}
	};
	function Gh(e) {
		this._internalRoot = e;
	}
	Gh.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = vt();
			e = {
				blockedOn: null,
				target: e,
				priority: t
			};
			for (var n = 0; n < Ah.length && t !== 0 && t < Ah[n].priority; n++);
			Ah.splice(n, 0, e), n === 0 && Fh(e);
		}
	};
	var Kh = n.version;
	if (Kh !== "19.3.0") throw Error(i(527, Kh, "19.3.0"));
	L.findDOMNode = function(e) {
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(i(188)) : (e = Object.keys(e).join(","), Error(i(268, e)));
		return e = u(t), e = e === null ? null : d(e), e = e === null ? null : e.stateNode, e;
	};
	var qh = {
		bundleType: 0,
		version: "19.3.0",
		rendererPackageName: "react-dom",
		currentDispatcherRef: I,
		reconcilerVersion: "19.3.0"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var Jh = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!Jh.isDisabled && Jh.supportsFiber) try {
			Je = Jh.inject(qh), Ye = Jh;
		} catch {}
	}
	e.createRoot = function(e, t) {
		if (!a(e)) throw Error(i(299));
		var n = !1, r = "", o = bc, s = xc, c = Sc;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (r = t.identifierPrefix), t.onUncaughtError !== void 0 && (o = t.onUncaughtError), t.onCaughtError !== void 0 && (s = t.onCaughtError), t.onRecoverableError !== void 0 && (c = t.onRecoverableError)), t = lh(e, 1, !1, null, null, n, r, null, o, s, c, Uh), e[St] = t.current, Uf(e), new Wh(t);
	};
})), cu = (/* @__PURE__ */ p(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = su();
})))(), lu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => b.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, b.createElement("path", { d: "M13.1717 12.0007L8.22192 7.05093L9.63614 5.63672L16.0001 12.0007L9.63614 18.3646L8.22192 16.9504L13.1717 12.0007Z" })), uu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => b.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, b.createElement("path", { d: "M11.9997 10.5865L16.9495 5.63672L18.3637 7.05093L13.4139 12.0007L18.3637 16.9504L16.9495 18.3646L11.9997 13.4149L7.04996 18.3646L5.63574 16.9504L10.5855 12.0007L5.63574 7.05093L7.04996 5.63672L11.9997 10.5865Z" })), du = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => b.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, b.createElement("path", { d: "M10 6V8H5V19H16V14H18V20C18 20.5523 17.5523 21 17 21H4C3.44772 21 3 20.5523 3 20V7C3 6.44772 3.44772 6 4 6H10ZM21 3V11H19L18.9999 6.413L11.2071 14.2071L9.79289 12.7929L17.5849 5H13V3H21Z" })), fu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => b.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, b.createElement("path", { d: "M12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12H4C4 16.4183 7.58172 20 12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C9.25022 4 6.82447 5.38734 5.38451 7.50024L8 7.5V9.5H2V3.5H4L3.99989 5.99918C5.82434 3.57075 8.72873 2 12 2ZM13 7L12.9998 11.585L16.2426 14.8284L14.8284 16.2426L10.9998 12.413L11 7H13Z" })), pu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => b.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, b.createElement("path", { d: "M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM11 11V17H13V11H11ZM11 7V9H13V7H11Z" })), mu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => b.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, b.createElement("path", { d: "M14 4.4375C15.3462 4.4375 16.4375 3.34619 16.4375 2H17.5625C17.5625 3.34619 18.6538 4.4375 20 4.4375V5.5625C18.6538 5.5625 17.5625 6.65381 17.5625 8H16.4375C16.4375 6.65381 15.3462 5.5625 14 5.5625V4.4375ZM1 11C4.31371 11 7 8.31371 7 5H9C9 8.31371 11.6863 11 15 11V13C11.6863 13 9 15.6863 9 19H7C7 15.6863 4.31371 13 1 13V11ZM4.87601 12C6.18717 12.7276 7.27243 13.8128 8 15.124 8.72757 13.8128 9.81283 12.7276 11.124 12 9.81283 11.2724 8.72757 10.1872 8 8.87601 7.27243 10.1872 6.18717 11.2724 4.87601 12ZM17.25 14C17.25 15.7949 15.7949 17.25 14 17.25V18.75C15.7949 18.75 17.25 20.2051 17.25 22H18.75C18.75 20.2051 20.2051 18.75 22 18.75V17.25C20.2051 17.25 18.75 15.7949 18.75 14H17.25Z" })), hu = (e, t) => {
	let n = Array(e.length + t.length);
	for (let t = 0; t < e.length; t++) n[t] = e[t];
	for (let r = 0; r < t.length; r++) n[e.length + r] = t[r];
	return n;
}, gu = (e, t) => ({
	classGroupId: e,
	validator: t
}), _u = (e = /* @__PURE__ */ new Map(), t = null, n) => ({
	nextPart: e,
	validators: t,
	classGroupId: n
}), vu = "-", yu = [], bu = "arbitrary..", xu = (e) => {
	let t = wu(e), { conflictingClassGroups: n, conflictingClassGroupModifiers: r } = e;
	return {
		getClassGroupId: (e) => {
			if (e.startsWith("[") && e.endsWith("]")) return Cu(e);
			let n = e.split(vu);
			return Su(n, +(n[0] === "" && n.length > 1), t);
		},
		getConflictingClassGroupIds: (e, t) => {
			if (t) {
				let t = r[e], i = n[e];
				return t ? i ? hu(i, t) : t : i || yu;
			}
			return n[e] || yu;
		}
	};
}, Su = (e, t, n) => {
	if (e.length - t === 0) return n.classGroupId;
	let r = e[t], i = n.nextPart.get(r);
	if (i) {
		let n = Su(e, t + 1, i);
		if (n) return n;
	}
	let a = n.validators;
	if (a === null) return;
	let o = t === 0 ? e.join(vu) : e.slice(t).join(vu), s = a.length;
	for (let e = 0; e < s; e++) {
		let t = a[e];
		if (t.validator(o)) return t.classGroupId;
	}
}, Cu = (e) => e.slice(1, -1).indexOf(":") === -1 ? void 0 : (() => {
	let t = e.slice(1, -1), n = t.indexOf(":"), r = t.slice(0, n);
	return r ? bu + r : void 0;
})(), wu = (e) => {
	let { theme: t, classGroups: n } = e;
	return Tu(n, t);
}, Tu = (e, t) => {
	let n = _u();
	for (let r in e) {
		let i = e[r];
		Eu(i, n, r, t);
	}
	return n;
}, Eu = (e, t, n, r) => {
	let i = e.length;
	for (let a = 0; a < i; a++) {
		let i = e[a];
		Du(i, t, n, r);
	}
}, Du = (e, t, n, r) => {
	if (typeof e == "string") {
		Ou(e, t, n);
		return;
	}
	if (typeof e == "function") {
		ku(e, t, n, r);
		return;
	}
	Au(e, t, n, r);
}, Ou = (e, t, n) => {
	let r = e === "" ? t : ju(t, e);
	r.classGroupId = n;
}, ku = (e, t, n, r) => {
	if (Mu(e)) {
		Eu(e(r), t, n, r);
		return;
	}
	t.validators === null && (t.validators = []), t.validators.push(gu(n, e));
}, Au = (e, t, n, r) => {
	let i = Object.entries(e), a = i.length;
	for (let e = 0; e < a; e++) {
		let [a, o] = i[e];
		Eu(o, ju(t, a), n, r);
	}
}, ju = (e, t) => {
	let n = e, r = t.split(vu), i = r.length;
	for (let e = 0; e < i; e++) {
		let t = r[e], i = n.nextPart.get(t);
		i || (i = _u(), n.nextPart.set(t, i)), n = i;
	}
	return n;
}, Mu = (e) => "isThemeGetter" in e && e.isThemeGetter === !0, Nu = (e) => {
	if (e < 1) return {
		get: () => void 0,
		set: () => {}
	};
	let t = 0, n = Object.create(null), r = Object.create(null), i = (i, a) => {
		n[i] = a, t++, t > e && (t = 0, r = n, n = Object.create(null));
	};
	return {
		get(e) {
			let t = n[e];
			if (t !== void 0) return t;
			if ((t = r[e]) !== void 0) return i(e, t), t;
		},
		set(e, t) {
			e in n ? n[e] = t : i(e, t);
		}
	};
}, Pu = "!", Fu = ":", Iu = [], Lu = (e, t, n, r, i) => ({
	modifiers: e,
	hasImportantModifier: t,
	baseClassName: n,
	maybePostfixModifierPosition: r,
	isExternal: i
}), Ru = (e) => {
	let { prefix: t, experimentalParseClassName: n } = e, r = (e) => {
		let t = [], n = 0, r = 0, i = 0, a, o = e.length;
		for (let s = 0; s < o; s++) {
			let o = e[s];
			if (n === 0 && r === 0) {
				if (o === Fu) {
					t.push(e.slice(i, s)), i = s + 1;
					continue;
				}
				if (o === "/") {
					a = s;
					continue;
				}
			}
			o === "[" ? n++ : o === "]" ? n-- : o === "(" ? r++ : o === ")" && r--;
		}
		let s = t.length === 0 ? e : e.slice(i), c = s, l = !1;
		s.endsWith(Pu) ? (c = s.slice(0, -1), l = !0) : s.startsWith(Pu) && (c = s.slice(1), l = !0);
		let u = a && a > i ? a - i : void 0;
		return Lu(t, l, c, u);
	};
	if (t) {
		let e = t + Fu, n = r;
		r = (t) => t.startsWith(e) ? n(t.slice(e.length)) : Lu(Iu, !1, t, void 0, !0);
	}
	if (n) {
		let e = r;
		r = (t) => n({
			className: t,
			parseClassName: e
		});
	}
	return r;
}, zu = (e) => {
	let t = /* @__PURE__ */ new Map();
	return e.orderSensitiveModifiers.forEach((e, n) => {
		t.set(e, 1e6 + n);
	}), (e) => {
		let n = [], r = [];
		for (let i = 0; i < e.length; i++) {
			let a = e[i], o = a[0] === "[", s = t.has(a);
			o || s ? (r.length > 0 && (r.sort(), n.push(...r), r = []), n.push(a)) : r.push(a);
		}
		return r.length > 0 && (r.sort(), n.push(...r)), n;
	};
}, Bu = (e) => ({
	cache: Nu(e.cacheSize),
	parseClassName: Ru(e),
	sortModifiers: zu(e),
	postfixLookupClassGroupIds: Vu(e),
	...xu(e)
}), Vu = (e) => {
	let t = Object.create(null), n = e.postfixLookupClassGroups;
	if (n) for (let e = 0; e < n.length; e++) t[n[e]] = !0;
	return t;
}, Hu = /\s+/, Uu = (e, t) => {
	let { parseClassName: n, getClassGroupId: r, getConflictingClassGroupIds: i, sortModifiers: a, postfixLookupClassGroupIds: o } = t, s = [], c = e.trim().split(Hu), l = "";
	for (let e = c.length - 1; e >= 0; --e) {
		let t = c[e], { isExternal: u, modifiers: d, hasImportantModifier: f, baseClassName: p, maybePostfixModifierPosition: m } = n(t);
		if (u) {
			l = t + (l.length > 0 ? " " + l : l);
			continue;
		}
		let h = !!m, g;
		if (h) {
			g = r(p.substring(0, m));
			let e = g && o[g] ? r(p) : void 0;
			e && e !== g && (g = e, h = !1);
		} else g = r(p);
		if (!g) {
			if (!h) {
				l = t + (l.length > 0 ? " " + l : l);
				continue;
			}
			if (g = r(p), !g) {
				l = t + (l.length > 0 ? " " + l : l);
				continue;
			}
			h = !1;
		}
		let _ = d.length === 0 ? "" : d.length === 1 ? d[0] : a(d).join(":"), v = f ? _ + Pu : _, y = v + g;
		if (s.indexOf(y) > -1) continue;
		s.push(y);
		let b = i(g, h);
		for (let e = 0; e < b.length; ++e) {
			let t = b[e];
			s.push(v + t);
		}
		l = t + (l.length > 0 ? " " + l : l);
	}
	return l;
}, Wu = (...e) => {
	let t = 0, n, r, i = "";
	for (; t < e.length;) (n = e[t++]) && (r = Gu(n)) && (i && (i += " "), i += r);
	return i;
}, Gu = (e) => {
	if (typeof e == "string") return e;
	let t, n = "";
	for (let r = 0; r < e.length; r++) e[r] && (t = Gu(e[r])) && (n && (n += " "), n += t);
	return n;
}, Ku = (e, ...t) => {
	let n, r, i, a, o = (o) => (n = Bu(t.reduce((e, t) => t(e), e())), r = n.cache.get, i = n.cache.set, a = s, s(o)), s = (e) => {
		let t = r(e);
		if (t) return t;
		let a = Uu(e, n);
		return i(e, a), a;
	};
	return a = o, (...e) => a(Wu(...e));
}, qu = [], Ju = (e) => {
	let t = (t) => t[e] || qu;
	return t.isThemeGetter = !0, t.themeKey = e, t;
}, Yu = /^\[(?:(\w[\w-]*):)?(.+)\]$/i, Xu = /^\((?:(\w[\w-]*):)?(.+)\)$/i, Zu = /^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/, Qu = /^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/, $u = /\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/, ed = /^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix|color|light-dark)\(.+\)$/, q = /^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/, J = /^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/, Y = (e) => Zu.test(e), X = (e) => !!e && !Number.isNaN(Number(e)), td = (e) => !!e && Number.isInteger(Number(e)), nd = (e) => e.endsWith("%") && X(e.slice(0, -1)), rd = (e) => Qu.test(e), id = () => !0, ad = (e) => $u.test(e) && !ed.test(e), od = () => !1, sd = (e) => q.test(e), cd = (e) => J.test(e), ld = (e) => !Z(e) && !Q(e), ud = (e) => e.startsWith("@container") && (e[10] === "/" && e[11] !== void 0 || e[11] === "s" && e[16] !== void 0 && e.startsWith("-size/", 10) || e[11] === "n" && e[18] !== void 0 && e.startsWith("-normal/", 10)), dd = (e) => Ed(e, Ad, od), Z = (e) => Yu.test(e), fd = (e) => Ed(e, jd, ad), pd = (e) => Ed(e, Md, X), md = (e) => Ed(e, Pd, id), hd = (e) => Ed(e, Nd, od), gd = (e) => Ed(e, Od, od), _d = (e) => Ed(e, kd, cd), vd = (e) => Ed(e, Fd, sd), Q = (e) => Xu.test(e), yd = (e) => Dd(e, jd), bd = (e) => Dd(e, Nd), xd = (e) => Dd(e, Od), Sd = (e) => Dd(e, Ad), Cd = (e) => Dd(e, kd), wd = (e) => Dd(e, Fd, !0), Td = (e) => Dd(e, Pd, !0), Ed = (e, t, n) => {
	let r = Yu.exec(e);
	return r ? r[1] ? t(r[1]) : n(r[2]) : !1;
}, Dd = (e, t, n = !1) => {
	let r = Xu.exec(e);
	return r ? r[1] ? t(r[1]) : n : !1;
}, Od = (e) => e === "position" || e === "percentage", kd = (e) => e === "image" || e === "url", Ad = (e) => e === "length" || e === "size" || e === "bg-size", jd = (e) => e === "length", Md = (e) => e === "number", Nd = (e) => e === "family-name", Pd = (e) => e === "number" || e === "weight", Fd = (e) => e === "shadow", Id = () => {
	let e = Ju("color"), t = Ju("font"), n = Ju("text"), r = Ju("font-weight"), i = Ju("tracking"), a = Ju("leading"), o = Ju("breakpoint"), s = Ju("container"), c = Ju("spacing"), l = Ju("radius"), u = Ju("shadow"), d = Ju("inset-shadow"), f = Ju("text-shadow"), p = Ju("drop-shadow"), m = Ju("blur"), h = Ju("perspective"), g = Ju("aspect"), _ = Ju("ease"), v = Ju("animate"), y = () => [
		"auto",
		"avoid",
		"all",
		"avoid-page",
		"page",
		"left",
		"right",
		"column"
	], b = () => [
		"center",
		"top",
		"bottom",
		"left",
		"right",
		"top-left",
		"left-top",
		"top-right",
		"right-top",
		"bottom-right",
		"right-bottom",
		"bottom-left",
		"left-bottom"
	], x = () => [
		...b(),
		Q,
		Z
	], S = () => [
		"auto",
		"hidden",
		"clip",
		"visible",
		"scroll"
	], C = () => [
		"auto",
		"contain",
		"none"
	], w = () => [
		Q,
		Z,
		c
	], T = () => [
		Y,
		"full",
		"auto",
		...w()
	], E = () => [
		td,
		"none",
		"subgrid",
		Q,
		Z
	], D = () => [
		"auto",
		{ span: [
			"full",
			td,
			Q,
			Z
		] },
		td,
		Q,
		Z
	], O = () => [
		td,
		"auto",
		Q,
		Z
	], k = () => [
		"auto",
		"min",
		"max",
		"fr",
		Q,
		Z
	], A = () => [
		"start",
		"end",
		"center",
		"between",
		"around",
		"evenly",
		"stretch",
		"baseline",
		"center-safe",
		"end-safe"
	], j = () => [
		"start",
		"end",
		"center",
		"stretch",
		"center-safe",
		"end-safe"
	], M = () => ["auto", ...w()], N = () => [
		Y,
		"auto",
		"full",
		"dvw",
		"dvh",
		"lvw",
		"lvh",
		"svw",
		"svh",
		"min",
		"max",
		"fit",
		...w()
	], ee = () => [
		s,
		Y,
		"screen",
		"full",
		"dvw",
		"lvw",
		"svw",
		"min",
		"max",
		"fit",
		...w()
	], te = () => [
		Y,
		"screen",
		"full",
		"lh",
		"dvh",
		"lvh",
		"svh",
		"min",
		"max",
		"fit",
		...w()
	], P = () => [
		e,
		Q,
		Z
	], ne = () => [
		...b(),
		xd,
		gd,
		{ position: [Q, Z] }
	], F = () => ["no-repeat", { repeat: [
		"",
		"x",
		"y",
		"space",
		"round"
	] }], re = () => [
		"auto",
		"cover",
		"contain",
		Sd,
		dd,
		{ size: [Q, Z] }
	], ie = () => [
		nd,
		yd,
		fd
	], ae = () => [
		"",
		"none",
		"full",
		l,
		Q,
		Z
	], oe = () => [
		"",
		X,
		yd,
		fd
	], se = () => [
		"solid",
		"dashed",
		"dotted",
		"double"
	], ce = () => [
		"normal",
		"multiply",
		"screen",
		"overlay",
		"darken",
		"lighten",
		"color-dodge",
		"color-burn",
		"hard-light",
		"soft-light",
		"difference",
		"exclusion",
		"hue",
		"saturation",
		"color",
		"luminosity"
	], le = () => [
		X,
		nd,
		xd,
		gd
	], ue = () => [
		"",
		"none",
		m,
		Q,
		Z
	], de = () => [
		"none",
		X,
		Q,
		Z
	], fe = () => [
		"none",
		X,
		Q,
		Z
	], I = () => [
		X,
		Q,
		Z
	], L = () => [
		Y,
		"full",
		...w()
	];
	return {
		cacheSize: 500,
		theme: {
			animate: [
				"spin",
				"ping",
				"pulse",
				"bounce"
			],
			aspect: ["video"],
			blur: [rd],
			breakpoint: [rd],
			color: [id],
			container: [rd],
			"drop-shadow": [rd],
			ease: [
				"in",
				"out",
				"in-out"
			],
			font: [ld],
			"font-weight": [
				"thin",
				"extralight",
				"light",
				"normal",
				"medium",
				"semibold",
				"bold",
				"extrabold",
				"black"
			],
			"inset-shadow": [rd],
			leading: [
				"none",
				"tight",
				"snug",
				"normal",
				"relaxed",
				"loose"
			],
			perspective: [
				"dramatic",
				"near",
				"normal",
				"midrange",
				"distant",
				"none"
			],
			radius: [rd],
			shadow: [rd],
			spacing: ["px", X],
			text: [rd],
			"text-shadow": [rd],
			tracking: [
				"tighter",
				"tight",
				"normal",
				"wide",
				"wider",
				"widest"
			]
		},
		classGroups: {
			aspect: [{ aspect: [
				"auto",
				"square",
				Y,
				Z,
				Q,
				g
			] }],
			container: ["container"],
			"container-type": [{ "@container": [
				"",
				"normal",
				"size",
				Q,
				Z
			] }],
			"container-named": [ud],
			columns: [{ columns: [
				X,
				"auto",
				Z,
				Q,
				s
			] }],
			"break-after": [{ "break-after": y() }],
			"break-before": [{ "break-before": y() }],
			"break-inside": [{ "break-inside": [
				"auto",
				"avoid",
				"avoid-page",
				"avoid-column"
			] }],
			"box-decoration": [{ "box-decoration": ["slice", "clone"] }],
			box: [{ box: ["border", "content"] }],
			display: [
				"block",
				"inline-block",
				"inline",
				"flex",
				"inline-flex",
				"table",
				"inline-table",
				"table-caption",
				"table-cell",
				"table-column",
				"table-column-group",
				"table-footer-group",
				"table-header-group",
				"table-row-group",
				"table-row",
				"flow-root",
				"grid",
				"inline-grid",
				"contents",
				"list-item",
				"hidden"
			],
			sr: ["sr-only", "not-sr-only"],
			float: [{ float: [
				"right",
				"left",
				"none",
				"start",
				"end"
			] }],
			clear: [{ clear: [
				"left",
				"right",
				"both",
				"none",
				"start",
				"end"
			] }],
			isolation: ["isolate", "isolation-auto"],
			"object-fit": [{ object: [
				"contain",
				"cover",
				"fill",
				"none",
				"scale-down"
			] }],
			"object-position": [{ object: x() }],
			overflow: [{ overflow: S() }],
			"overflow-x": [{ "overflow-x": S() }],
			"overflow-y": [{ "overflow-y": S() }],
			overscroll: [{ overscroll: C() }],
			"overscroll-x": [{ "overscroll-x": C() }],
			"overscroll-y": [{ "overscroll-y": C() }],
			position: [
				"static",
				"fixed",
				"absolute",
				"relative",
				"sticky"
			],
			inset: [{ inset: T() }],
			"inset-x": [{ "inset-x": T() }],
			"inset-y": [{ "inset-y": T() }],
			start: [{
				"inset-s": T(),
				start: T()
			}],
			end: [{
				"inset-e": T(),
				end: T()
			}],
			"inset-bs": [{ "inset-bs": T() }],
			"inset-be": [{ "inset-be": T() }],
			top: [{ top: T() }],
			right: [{ right: T() }],
			bottom: [{ bottom: T() }],
			left: [{ left: T() }],
			visibility: [
				"visible",
				"invisible",
				"collapse"
			],
			z: [{ z: [
				td,
				"auto",
				Q,
				Z
			] }],
			basis: [{ basis: [
				Y,
				"full",
				"auto",
				s,
				...w()
			] }],
			"flex-direction": [{ flex: [
				"row",
				"row-reverse",
				"col",
				"col-reverse"
			] }],
			"flex-wrap": [{ flex: [
				"nowrap",
				"wrap",
				"wrap-reverse"
			] }],
			flex: [{ flex: [
				X,
				Y,
				"auto",
				"initial",
				"none",
				Z
			] }],
			grow: [{ grow: [
				"",
				X,
				Q,
				Z
			] }],
			shrink: [{ shrink: [
				"",
				X,
				Q,
				Z
			] }],
			order: [{ order: [
				td,
				"first",
				"last",
				"none",
				Q,
				Z
			] }],
			"grid-cols": [{ "grid-cols": E() }],
			"col-start-end": [{ col: D() }],
			"col-start": [{ "col-start": O() }],
			"col-end": [{ "col-end": O() }],
			"grid-rows": [{ "grid-rows": E() }],
			"row-start-end": [{ row: D() }],
			"row-start": [{ "row-start": O() }],
			"row-end": [{ "row-end": O() }],
			"grid-flow": [{ "grid-flow": [
				"row",
				"col",
				"dense",
				"row-dense",
				"col-dense"
			] }],
			"auto-cols": [{ "auto-cols": k() }],
			"auto-rows": [{ "auto-rows": k() }],
			gap: [{ gap: w() }],
			"gap-x": [{ "gap-x": w() }],
			"gap-y": [{ "gap-y": w() }],
			"justify-content": [{ justify: [...A(), "normal"] }],
			"justify-items": [{ "justify-items": [...j(), "normal"] }],
			"justify-self": [{ "justify-self": ["auto", ...j()] }],
			"align-content": [{ content: ["normal", ...A()] }],
			"align-items": [{ items: [...j(), { baseline: ["", "last"] }] }],
			"align-self": [{ self: [
				"auto",
				...j(),
				{ baseline: ["", "last"] }
			] }],
			"place-content": [{ "place-content": A() }],
			"place-items": [{ "place-items": [...j(), "baseline"] }],
			"place-self": [{ "place-self": ["auto", ...j()] }],
			p: [{ p: w() }],
			px: [{ px: w() }],
			py: [{ py: w() }],
			ps: [{ ps: w() }],
			pe: [{ pe: w() }],
			pbs: [{ pbs: w() }],
			pbe: [{ pbe: w() }],
			pt: [{ pt: w() }],
			pr: [{ pr: w() }],
			pb: [{ pb: w() }],
			pl: [{ pl: w() }],
			m: [{ m: M() }],
			mx: [{ mx: M() }],
			my: [{ my: M() }],
			ms: [{ ms: M() }],
			me: [{ me: M() }],
			mbs: [{ mbs: M() }],
			mbe: [{ mbe: M() }],
			mt: [{ mt: M() }],
			mr: [{ mr: M() }],
			mb: [{ mb: M() }],
			ml: [{ ml: M() }],
			"space-x": [{ "space-x": w() }],
			"space-x-reverse": ["space-x-reverse"],
			"space-y": [{ "space-y": w() }],
			"space-y-reverse": ["space-y-reverse"],
			size: [{ size: N() }],
			"inline-size": [{ inline: ["auto", ...ee()] }],
			"min-inline-size": [{ "min-inline": ["auto", ...ee()] }],
			"max-inline-size": [{ "max-inline": ["none", ...ee()] }],
			"block-size": [{ block: ["auto", ...te()] }],
			"min-block-size": [{ "min-block": ["auto", ...te()] }],
			"max-block-size": [{ "max-block": ["none", ...te()] }],
			w: [{ w: [
				s,
				"screen",
				...N()
			] }],
			"min-w": [{ "min-w": [
				s,
				"screen",
				"none",
				...N()
			] }],
			"max-w": [{ "max-w": [
				s,
				"screen",
				"none",
				"prose",
				{ screen: [o] },
				...N()
			] }],
			h: [{ h: [
				"screen",
				"lh",
				...N()
			] }],
			"min-h": [{ "min-h": [
				"screen",
				"lh",
				"none",
				...N()
			] }],
			"max-h": [{ "max-h": [
				"screen",
				"lh",
				"none",
				...N()
			] }],
			"font-size": [{ text: [
				"base",
				n,
				yd,
				fd
			] }],
			"font-smoothing": ["antialiased", "subpixel-antialiased"],
			"font-style": ["italic", "not-italic"],
			"font-weight": [{ font: [
				r,
				Td,
				md
			] }],
			"font-stretch": [{ "font-stretch": [
				"ultra-condensed",
				"extra-condensed",
				"condensed",
				"semi-condensed",
				"normal",
				"semi-expanded",
				"expanded",
				"extra-expanded",
				"ultra-expanded",
				nd,
				Z
			] }],
			"font-family": [{ font: [
				bd,
				hd,
				t
			] }],
			"font-features": [{ "font-features": [Z] }],
			"fvn-normal": ["normal-nums"],
			"fvn-ordinal": ["ordinal"],
			"fvn-slashed-zero": ["slashed-zero"],
			"fvn-figure": ["lining-nums", "oldstyle-nums"],
			"fvn-spacing": ["proportional-nums", "tabular-nums"],
			"fvn-fraction": ["diagonal-fractions", "stacked-fractions"],
			tracking: [{ tracking: [
				i,
				Q,
				Z
			] }],
			"line-clamp": [{ "line-clamp": [
				X,
				"none",
				Q,
				pd
			] }],
			leading: [{ leading: [
				"none",
				a,
				...w()
			] }],
			"list-image": [{ "list-image": [
				"none",
				Q,
				Z
			] }],
			"list-style-position": [{ list: ["inside", "outside"] }],
			"list-style-type": [{ list: [
				"disc",
				"decimal",
				"none",
				Q,
				Z
			] }],
			"text-alignment": [{ text: [
				"left",
				"center",
				"right",
				"justify",
				"start",
				"end"
			] }],
			"placeholder-color": [{ placeholder: P() }],
			"text-color": [{ text: P() }],
			"text-decoration": [
				"underline",
				"overline",
				"line-through",
				"no-underline"
			],
			"text-decoration-style": [{ decoration: [...se(), "wavy"] }],
			"text-decoration-thickness": [{ decoration: [
				X,
				"from-font",
				"auto",
				Q,
				fd
			] }],
			"text-decoration-color": [{ decoration: P() }],
			"underline-offset": [{ "underline-offset": [
				X,
				"auto",
				Q,
				Z
			] }],
			"text-transform": [
				"uppercase",
				"lowercase",
				"capitalize",
				"normal-case"
			],
			"text-overflow": [
				"truncate",
				"text-ellipsis",
				"text-clip"
			],
			"text-wrap": [{ text: [
				"wrap",
				"nowrap",
				"balance",
				"pretty"
			] }],
			indent: [{ indent: w() }],
			"tab-size": [{ tab: [
				td,
				Q,
				Z
			] }],
			"vertical-align": [{ align: [
				"baseline",
				"top",
				"middle",
				"bottom",
				"text-top",
				"text-bottom",
				"sub",
				"super",
				Q,
				Z
			] }],
			whitespace: [{ whitespace: [
				"normal",
				"nowrap",
				"pre",
				"pre-line",
				"pre-wrap",
				"break-spaces"
			] }],
			break: [{ break: [
				"normal",
				"words",
				"all",
				"keep"
			] }],
			wrap: [{ wrap: [
				"break-word",
				"anywhere",
				"normal"
			] }],
			hyphens: [{ hyphens: [
				"none",
				"manual",
				"auto"
			] }],
			content: [{ content: [
				"none",
				Q,
				Z
			] }],
			"bg-attachment": [{ bg: [
				"fixed",
				"local",
				"scroll"
			] }],
			"bg-clip": [{ "bg-clip": [
				"border",
				"padding",
				"content",
				"text"
			] }],
			"bg-origin": [{ "bg-origin": [
				"border",
				"padding",
				"content"
			] }],
			"bg-position": [{ bg: ne() }],
			"bg-repeat": [{ bg: F() }],
			"bg-size": [{ bg: re() }],
			"bg-image": [{ bg: [
				"none",
				{
					linear: [
						{ to: [
							"t",
							"tr",
							"r",
							"br",
							"b",
							"bl",
							"l",
							"tl"
						] },
						td,
						Q,
						Z
					],
					radial: [
						"",
						Q,
						Z
					],
					conic: [
						"",
						td,
						Q,
						Z
					]
				},
				Cd,
				_d
			] }],
			"bg-color": [{ bg: P() }],
			"gradient-from-pos": [{ from: ie() }],
			"gradient-via-pos": [{ via: ie() }],
			"gradient-to-pos": [{ to: ie() }],
			"gradient-from": [{ from: P() }],
			"gradient-via": [{ via: P() }],
			"gradient-to": [{ to: P() }],
			rounded: [{ rounded: ae() }],
			"rounded-s": [{ "rounded-s": ae() }],
			"rounded-e": [{ "rounded-e": ae() }],
			"rounded-t": [{ "rounded-t": ae() }],
			"rounded-r": [{ "rounded-r": ae() }],
			"rounded-b": [{ "rounded-b": ae() }],
			"rounded-l": [{ "rounded-l": ae() }],
			"rounded-ss": [{ "rounded-ss": ae() }],
			"rounded-se": [{ "rounded-se": ae() }],
			"rounded-ee": [{ "rounded-ee": ae() }],
			"rounded-es": [{ "rounded-es": ae() }],
			"rounded-tl": [{ "rounded-tl": ae() }],
			"rounded-tr": [{ "rounded-tr": ae() }],
			"rounded-br": [{ "rounded-br": ae() }],
			"rounded-bl": [{ "rounded-bl": ae() }],
			"border-w": [{ border: oe() }],
			"border-w-x": [{ "border-x": oe() }],
			"border-w-y": [{ "border-y": oe() }],
			"border-w-s": [{ "border-s": oe() }],
			"border-w-e": [{ "border-e": oe() }],
			"border-w-bs": [{ "border-bs": oe() }],
			"border-w-be": [{ "border-be": oe() }],
			"border-w-t": [{ "border-t": oe() }],
			"border-w-r": [{ "border-r": oe() }],
			"border-w-b": [{ "border-b": oe() }],
			"border-w-l": [{ "border-l": oe() }],
			"divide-x": [{ "divide-x": oe() }],
			"divide-x-reverse": ["divide-x-reverse"],
			"divide-y": [{ "divide-y": oe() }],
			"divide-y-reverse": ["divide-y-reverse"],
			"border-style": [{ border: [
				...se(),
				"hidden",
				"none"
			] }],
			"divide-style": [{ divide: [
				...se(),
				"hidden",
				"none"
			] }],
			"border-color": [{ border: P() }],
			"border-color-x": [{ "border-x": P() }],
			"border-color-y": [{ "border-y": P() }],
			"border-color-s": [{ "border-s": P() }],
			"border-color-e": [{ "border-e": P() }],
			"border-color-bs": [{ "border-bs": P() }],
			"border-color-be": [{ "border-be": P() }],
			"border-color-t": [{ "border-t": P() }],
			"border-color-r": [{ "border-r": P() }],
			"border-color-b": [{ "border-b": P() }],
			"border-color-l": [{ "border-l": P() }],
			"divide-color": [{ divide: P() }],
			"outline-style": [{ outline: [
				...se(),
				"none",
				"hidden"
			] }],
			"outline-offset": [{ "outline-offset": [
				X,
				Q,
				Z
			] }],
			"outline-w": [{ outline: [
				"",
				X,
				yd,
				fd
			] }],
			"outline-color": [{ outline: P() }],
			shadow: [{ shadow: [
				"",
				"inner",
				"none",
				u,
				wd,
				vd
			] }],
			"shadow-color": [{ shadow: P() }],
			"inset-shadow": [{ "inset-shadow": [
				"none",
				d,
				wd,
				vd
			] }],
			"inset-shadow-color": [{ "inset-shadow": P() }],
			"ring-w": [{ ring: oe() }],
			"ring-w-inset": ["ring-inset"],
			"ring-color": [{ ring: P() }],
			"ring-offset-w": [{ "ring-offset": [X, fd] }],
			"ring-offset-color": [{ "ring-offset": P() }],
			"inset-ring-w": [{ "inset-ring": oe() }],
			"inset-ring-color": [{ "inset-ring": P() }],
			"text-shadow": [{ "text-shadow": [
				"none",
				f,
				wd,
				vd
			] }],
			"text-shadow-color": [{ "text-shadow": P() }],
			opacity: [{ opacity: [
				X,
				Q,
				Z
			] }],
			"mix-blend": [{ "mix-blend": [
				...ce(),
				"plus-darker",
				"plus-lighter"
			] }],
			"bg-blend": [{ "bg-blend": ce() }],
			"mask-clip": [{ "mask-clip": [
				"border",
				"padding",
				"content",
				"fill",
				"stroke",
				"view"
			] }, "mask-no-clip"],
			"mask-composite": [{ mask: [
				"add",
				"subtract",
				"intersect",
				"exclude"
			] }],
			"mask-image-linear-pos": [{ "mask-linear": [X] }],
			"mask-image-linear-from-pos": [{ "mask-linear-from": le() }],
			"mask-image-linear-to-pos": [{ "mask-linear-to": le() }],
			"mask-image-linear-from-color": [{ "mask-linear-from": P() }],
			"mask-image-linear-to-color": [{ "mask-linear-to": P() }],
			"mask-image-t-from-pos": [{ "mask-t-from": le() }],
			"mask-image-t-to-pos": [{ "mask-t-to": le() }],
			"mask-image-t-from-color": [{ "mask-t-from": P() }],
			"mask-image-t-to-color": [{ "mask-t-to": P() }],
			"mask-image-r-from-pos": [{ "mask-r-from": le() }],
			"mask-image-r-to-pos": [{ "mask-r-to": le() }],
			"mask-image-r-from-color": [{ "mask-r-from": P() }],
			"mask-image-r-to-color": [{ "mask-r-to": P() }],
			"mask-image-b-from-pos": [{ "mask-b-from": le() }],
			"mask-image-b-to-pos": [{ "mask-b-to": le() }],
			"mask-image-b-from-color": [{ "mask-b-from": P() }],
			"mask-image-b-to-color": [{ "mask-b-to": P() }],
			"mask-image-l-from-pos": [{ "mask-l-from": le() }],
			"mask-image-l-to-pos": [{ "mask-l-to": le() }],
			"mask-image-l-from-color": [{ "mask-l-from": P() }],
			"mask-image-l-to-color": [{ "mask-l-to": P() }],
			"mask-image-x-from-pos": [{ "mask-x-from": le() }],
			"mask-image-x-to-pos": [{ "mask-x-to": le() }],
			"mask-image-x-from-color": [{ "mask-x-from": P() }],
			"mask-image-x-to-color": [{ "mask-x-to": P() }],
			"mask-image-y-from-pos": [{ "mask-y-from": le() }],
			"mask-image-y-to-pos": [{ "mask-y-to": le() }],
			"mask-image-y-from-color": [{ "mask-y-from": P() }],
			"mask-image-y-to-color": [{ "mask-y-to": P() }],
			"mask-image-radial": [{ "mask-radial": [Q, Z] }],
			"mask-image-radial-from-pos": [{ "mask-radial-from": le() }],
			"mask-image-radial-to-pos": [{ "mask-radial-to": le() }],
			"mask-image-radial-from-color": [{ "mask-radial-from": P() }],
			"mask-image-radial-to-color": [{ "mask-radial-to": P() }],
			"mask-image-radial-shape": [{ "mask-radial": ["circle", "ellipse"] }],
			"mask-image-radial-size": [{ "mask-radial": [{
				closest: ["side", "corner"],
				farthest: ["side", "corner"]
			}] }],
			"mask-image-radial-pos": [{ "mask-radial-at": b() }],
			"mask-image-conic-pos": [{ "mask-conic": [X] }],
			"mask-image-conic-from-pos": [{ "mask-conic-from": le() }],
			"mask-image-conic-to-pos": [{ "mask-conic-to": le() }],
			"mask-image-conic-from-color": [{ "mask-conic-from": P() }],
			"mask-image-conic-to-color": [{ "mask-conic-to": P() }],
			"mask-mode": [{ mask: [
				"alpha",
				"luminance",
				"match"
			] }],
			"mask-origin": [{ "mask-origin": [
				"border",
				"padding",
				"content",
				"fill",
				"stroke",
				"view"
			] }],
			"mask-position": [{ mask: ne() }],
			"mask-repeat": [{ mask: F() }],
			"mask-size": [{ mask: re() }],
			"mask-type": [{ "mask-type": ["alpha", "luminance"] }],
			"mask-image": [{ mask: [
				"none",
				Q,
				Z
			] }],
			filter: [{ filter: [
				"",
				"none",
				Q,
				Z
			] }],
			blur: [{ blur: ue() }],
			brightness: [{ brightness: [
				X,
				Q,
				Z
			] }],
			contrast: [{ contrast: [
				X,
				Q,
				Z
			] }],
			"drop-shadow": [{ "drop-shadow": [
				"",
				"none",
				p,
				wd,
				vd
			] }],
			"drop-shadow-color": [{ "drop-shadow": P() }],
			grayscale: [{ grayscale: [
				"",
				X,
				Q,
				Z
			] }],
			"hue-rotate": [{ "hue-rotate": [
				X,
				Q,
				Z
			] }],
			invert: [{ invert: [
				"",
				X,
				Q,
				Z
			] }],
			saturate: [{ saturate: [
				X,
				Q,
				Z
			] }],
			sepia: [{ sepia: [
				"",
				X,
				Q,
				Z
			] }],
			"backdrop-filter": [{ "backdrop-filter": [
				"",
				"none",
				Q,
				Z
			] }],
			"backdrop-blur": [{ "backdrop-blur": ue() }],
			"backdrop-brightness": [{ "backdrop-brightness": [
				X,
				Q,
				Z
			] }],
			"backdrop-contrast": [{ "backdrop-contrast": [
				X,
				Q,
				Z
			] }],
			"backdrop-grayscale": [{ "backdrop-grayscale": [
				"",
				X,
				Q,
				Z
			] }],
			"backdrop-hue-rotate": [{ "backdrop-hue-rotate": [
				X,
				Q,
				Z
			] }],
			"backdrop-invert": [{ "backdrop-invert": [
				"",
				X,
				Q,
				Z
			] }],
			"backdrop-opacity": [{ "backdrop-opacity": [
				X,
				Q,
				Z
			] }],
			"backdrop-saturate": [{ "backdrop-saturate": [
				X,
				Q,
				Z
			] }],
			"backdrop-sepia": [{ "backdrop-sepia": [
				"",
				X,
				Q,
				Z
			] }],
			"border-collapse": [{ border: ["collapse", "separate"] }],
			"border-spacing": [{ "border-spacing": w() }],
			"border-spacing-x": [{ "border-spacing-x": w() }],
			"border-spacing-y": [{ "border-spacing-y": w() }],
			"table-layout": [{ table: ["auto", "fixed"] }],
			caption: [{ caption: ["top", "bottom"] }],
			transition: [{ transition: [
				"",
				"all",
				"colors",
				"opacity",
				"shadow",
				"transform",
				"none",
				Q,
				Z
			] }],
			"transition-behavior": [{ transition: ["normal", "discrete"] }],
			duration: [{ duration: [
				X,
				"initial",
				Q,
				Z
			] }],
			ease: [{ ease: [
				"linear",
				"initial",
				_,
				Q,
				Z
			] }],
			delay: [{ delay: [
				X,
				Q,
				Z
			] }],
			animate: [{ animate: [
				"none",
				v,
				Q,
				Z
			] }],
			backface: [{ backface: ["hidden", "visible"] }],
			perspective: [{ perspective: [
				h,
				Q,
				Z
			] }],
			"perspective-origin": [{ "perspective-origin": x() }],
			rotate: [{ rotate: de() }],
			"rotate-x": [{ "rotate-x": de() }],
			"rotate-y": [{ "rotate-y": de() }],
			"rotate-z": [{ "rotate-z": de() }],
			scale: [{ scale: fe() }],
			"scale-x": [{ "scale-x": fe() }],
			"scale-y": [{ "scale-y": fe() }],
			"scale-z": [{ "scale-z": fe() }],
			"scale-3d": ["scale-3d"],
			skew: [{ skew: I() }],
			"skew-x": [{ "skew-x": I() }],
			"skew-y": [{ "skew-y": I() }],
			transform: [{ transform: [
				Q,
				Z,
				"",
				"none",
				"gpu",
				"cpu"
			] }],
			"transform-origin": [{ origin: x() }],
			"transform-style": [{ transform: ["3d", "flat"] }],
			translate: [{ translate: L() }],
			"translate-x": [{ "translate-x": L() }],
			"translate-y": [{ "translate-y": L() }],
			"translate-z": [{ "translate-z": L() }],
			"translate-none": ["translate-none"],
			zoom: [{ zoom: [
				td,
				Q,
				Z
			] }],
			accent: [{ accent: P() }],
			appearance: [{ appearance: ["none", "auto"] }],
			"caret-color": [{ caret: P() }],
			"color-scheme": [{ scheme: [
				"normal",
				"dark",
				"light",
				"light-dark",
				"only-dark",
				"only-light"
			] }],
			cursor: [{ cursor: [
				"auto",
				"default",
				"pointer",
				"wait",
				"text",
				"move",
				"help",
				"not-allowed",
				"none",
				"context-menu",
				"progress",
				"cell",
				"crosshair",
				"vertical-text",
				"alias",
				"copy",
				"no-drop",
				"grab",
				"grabbing",
				"all-scroll",
				"col-resize",
				"row-resize",
				"n-resize",
				"e-resize",
				"s-resize",
				"w-resize",
				"ne-resize",
				"nw-resize",
				"se-resize",
				"sw-resize",
				"ew-resize",
				"ns-resize",
				"nesw-resize",
				"nwse-resize",
				"zoom-in",
				"zoom-out",
				Q,
				Z
			] }],
			"field-sizing": [{ "field-sizing": ["fixed", "content"] }],
			"pointer-events": [{ "pointer-events": ["auto", "none"] }],
			resize: [{ resize: [
				"none",
				"",
				"y",
				"x"
			] }],
			"scroll-behavior": [{ scroll: ["auto", "smooth"] }],
			"scrollbar-thumb-color": [{ "scrollbar-thumb": P() }],
			"scrollbar-track-color": [{ "scrollbar-track": P() }],
			"scrollbar-gutter": [{ "scrollbar-gutter": [
				"auto",
				"stable",
				"both"
			] }],
			"scrollbar-w": [{ scrollbar: [
				"auto",
				"thin",
				"none"
			] }],
			"scroll-m": [{ "scroll-m": w() }],
			"scroll-mx": [{ "scroll-mx": w() }],
			"scroll-my": [{ "scroll-my": w() }],
			"scroll-ms": [{ "scroll-ms": w() }],
			"scroll-me": [{ "scroll-me": w() }],
			"scroll-mbs": [{ "scroll-mbs": w() }],
			"scroll-mbe": [{ "scroll-mbe": w() }],
			"scroll-mt": [{ "scroll-mt": w() }],
			"scroll-mr": [{ "scroll-mr": w() }],
			"scroll-mb": [{ "scroll-mb": w() }],
			"scroll-ml": [{ "scroll-ml": w() }],
			"scroll-p": [{ "scroll-p": w() }],
			"scroll-px": [{ "scroll-px": w() }],
			"scroll-py": [{ "scroll-py": w() }],
			"scroll-ps": [{ "scroll-ps": w() }],
			"scroll-pe": [{ "scroll-pe": w() }],
			"scroll-pbs": [{ "scroll-pbs": w() }],
			"scroll-pbe": [{ "scroll-pbe": w() }],
			"scroll-pt": [{ "scroll-pt": w() }],
			"scroll-pr": [{ "scroll-pr": w() }],
			"scroll-pb": [{ "scroll-pb": w() }],
			"scroll-pl": [{ "scroll-pl": w() }],
			"snap-align": [{ snap: [
				"start",
				"end",
				"center",
				"align-none"
			] }],
			"snap-stop": [{ snap: ["normal", "always"] }],
			"snap-type": [{ snap: [
				"none",
				"x",
				"y",
				"both"
			] }],
			"snap-strictness": [{ snap: ["mandatory", "proximity"] }],
			touch: [{ touch: [
				"auto",
				"none",
				"manipulation"
			] }],
			"touch-x": [{ "touch-pan": [
				"x",
				"left",
				"right"
			] }],
			"touch-y": [{ "touch-pan": [
				"y",
				"up",
				"down"
			] }],
			"touch-pz": ["touch-pinch-zoom"],
			select: [{ select: [
				"none",
				"text",
				"all",
				"auto"
			] }],
			"will-change": [{ "will-change": [
				"auto",
				"scroll",
				"contents",
				"transform",
				Q,
				Z
			] }],
			fill: [{ fill: ["none", ...P()] }],
			"stroke-w": [{ stroke: [
				X,
				yd,
				fd,
				pd
			] }],
			stroke: [{ stroke: ["none", ...P()] }],
			"forced-color-adjust": [{ "forced-color-adjust": ["auto", "none"] }]
		},
		conflictingClassGroups: {
			"container-named": ["container-type"],
			overflow: ["overflow-x", "overflow-y"],
			overscroll: ["overscroll-x", "overscroll-y"],
			inset: [
				"inset-x",
				"inset-y",
				"inset-bs",
				"inset-be",
				"start",
				"end",
				"top",
				"right",
				"bottom",
				"left"
			],
			"inset-x": [
				"start",
				"end",
				"right",
				"left"
			],
			"inset-y": [
				"inset-bs",
				"inset-be",
				"top",
				"bottom"
			],
			flex: [
				"basis",
				"grow",
				"shrink"
			],
			gap: ["gap-x", "gap-y"],
			p: [
				"px",
				"py",
				"ps",
				"pe",
				"pbs",
				"pbe",
				"pt",
				"pr",
				"pb",
				"pl"
			],
			px: [
				"ps",
				"pe",
				"pr",
				"pl"
			],
			py: [
				"pbs",
				"pbe",
				"pt",
				"pb"
			],
			m: [
				"mx",
				"my",
				"ms",
				"me",
				"mbs",
				"mbe",
				"mt",
				"mr",
				"mb",
				"ml"
			],
			mx: [
				"ms",
				"me",
				"mr",
				"ml"
			],
			my: [
				"mbs",
				"mbe",
				"mt",
				"mb"
			],
			size: ["w", "h"],
			"font-size": ["leading"],
			"fvn-normal": [
				"fvn-ordinal",
				"fvn-slashed-zero",
				"fvn-figure",
				"fvn-spacing",
				"fvn-fraction"
			],
			"fvn-ordinal": ["fvn-normal"],
			"fvn-slashed-zero": ["fvn-normal"],
			"fvn-figure": ["fvn-normal"],
			"fvn-spacing": ["fvn-normal"],
			"fvn-fraction": ["fvn-normal"],
			"line-clamp": ["display", "overflow"],
			rounded: [
				"rounded-s",
				"rounded-e",
				"rounded-t",
				"rounded-r",
				"rounded-b",
				"rounded-l",
				"rounded-ss",
				"rounded-se",
				"rounded-ee",
				"rounded-es",
				"rounded-tl",
				"rounded-tr",
				"rounded-br",
				"rounded-bl"
			],
			"rounded-s": ["rounded-ss", "rounded-es"],
			"rounded-e": ["rounded-se", "rounded-ee"],
			"rounded-t": ["rounded-tl", "rounded-tr"],
			"rounded-r": ["rounded-tr", "rounded-br"],
			"rounded-b": ["rounded-br", "rounded-bl"],
			"rounded-l": ["rounded-tl", "rounded-bl"],
			"border-spacing": ["border-spacing-x", "border-spacing-y"],
			"border-w": [
				"border-w-x",
				"border-w-y",
				"border-w-s",
				"border-w-e",
				"border-w-bs",
				"border-w-be",
				"border-w-t",
				"border-w-r",
				"border-w-b",
				"border-w-l"
			],
			"border-w-x": [
				"border-w-s",
				"border-w-e",
				"border-w-r",
				"border-w-l"
			],
			"border-w-y": [
				"border-w-bs",
				"border-w-be",
				"border-w-t",
				"border-w-b"
			],
			"border-color": [
				"border-color-x",
				"border-color-y",
				"border-color-s",
				"border-color-e",
				"border-color-bs",
				"border-color-be",
				"border-color-t",
				"border-color-r",
				"border-color-b",
				"border-color-l"
			],
			"border-color-x": [
				"border-color-s",
				"border-color-e",
				"border-color-r",
				"border-color-l"
			],
			"border-color-y": [
				"border-color-bs",
				"border-color-be",
				"border-color-t",
				"border-color-b"
			],
			translate: [
				"translate-x",
				"translate-y",
				"translate-none"
			],
			"translate-none": [
				"translate",
				"translate-x",
				"translate-y",
				"translate-z"
			],
			"scroll-m": [
				"scroll-mx",
				"scroll-my",
				"scroll-ms",
				"scroll-me",
				"scroll-mbs",
				"scroll-mbe",
				"scroll-mt",
				"scroll-mr",
				"scroll-mb",
				"scroll-ml"
			],
			"scroll-mx": [
				"scroll-ms",
				"scroll-me",
				"scroll-mr",
				"scroll-ml"
			],
			"scroll-my": [
				"scroll-mbs",
				"scroll-mbe",
				"scroll-mt",
				"scroll-mb"
			],
			"scroll-p": [
				"scroll-px",
				"scroll-py",
				"scroll-ps",
				"scroll-pe",
				"scroll-pbs",
				"scroll-pbe",
				"scroll-pt",
				"scroll-pr",
				"scroll-pb",
				"scroll-pl"
			],
			"scroll-px": [
				"scroll-ps",
				"scroll-pe",
				"scroll-pr",
				"scroll-pl"
			],
			"scroll-py": [
				"scroll-pbs",
				"scroll-pbe",
				"scroll-pt",
				"scroll-pb"
			],
			touch: [
				"touch-x",
				"touch-y",
				"touch-pz"
			],
			"touch-x": ["touch"],
			"touch-y": ["touch"],
			"touch-pz": ["touch"]
		},
		conflictingClassGroupModifiers: { "font-size": ["leading"] },
		postfixLookupClassGroups: ["container-type"],
		orderSensitiveModifiers: [
			"*",
			"**",
			"after",
			"backdrop",
			"before",
			"details-content",
			"file",
			"first-letter",
			"first-line",
			"marker",
			"placeholder",
			"selection"
		]
	};
}, Ld = (e, { cacheSize: t, prefix: n, experimentalParseClassName: r, extend: i = {}, override: a = {} }) => (Rd(e, "cacheSize", t), Rd(e, "prefix", n), Rd(e, "experimentalParseClassName", r), zd(e.theme, a.theme), zd(e.classGroups, a.classGroups), zd(e.conflictingClassGroups, a.conflictingClassGroups), zd(e.conflictingClassGroupModifiers, a.conflictingClassGroupModifiers), Rd(e, "postfixLookupClassGroups", a.postfixLookupClassGroups), Rd(e, "orderSensitiveModifiers", a.orderSensitiveModifiers), Bd(e.theme, i.theme), Bd(e.classGroups, i.classGroups), Bd(e.conflictingClassGroups, i.conflictingClassGroups), Bd(e.conflictingClassGroupModifiers, i.conflictingClassGroupModifiers), Vd(e, i, "postfixLookupClassGroups"), Vd(e, i, "orderSensitiveModifiers"), e), Rd = (e, t, n) => {
	n !== void 0 && (e[t] = n);
}, zd = (e, t) => {
	if (t) for (let n in t) Rd(e, n, t[n]);
}, Bd = (e, t) => {
	if (t) for (let n in t) Vd(e, t, n);
}, Vd = (e, t, n) => {
	let r = t[n];
	r !== void 0 && (e[n] = e[n] ? e[n].concat(r) : r);
}, Hd = (e, ...t) => typeof e == "function" ? Ku(Id, e, ...t) : Ku(() => Ld(Id(), e), ...t), Ud = [
	"large-title",
	"display-1",
	"display-2",
	"display-3",
	"display-4",
	"title-1",
	"title-2",
	"title-3",
	"headline",
	"body",
	"body-2",
	"caption-1",
	"caption-2"
], Wd = [
	"regular",
	"medium",
	"semibold",
	"bold"
], Gd = Hd({ extend: { classGroups: { "font-size": [{ text: Ud.flatMap((e) => Wd.map((t) => `${e}-${t}`)) }] } } });
function Kd(e) {
	return e;
}
//#endregion
//#region src/react/boardui/components/base/badges/chip.tsx
var qd = Kd({
	base: "inline-flex items-center justify-center rounded-md px-1.5 whitespace-nowrap transition-[padding,font-size] duration-200 ease",
	variant: {
		bold: "py-0.5 text-body-medium",
		subtle: "py-1 text-body-medium",
		caption: "py-1 text-caption-1-medium"
	},
	color: {
		lime: "bg-status-lime-background text-status-lime-text",
		rose: "bg-status-rose-background text-status-rose-text",
		yellow: "bg-status-yellow-background text-status-yellow-text",
		cyan: "bg-status-cyan-background text-status-cyan-text",
		blue: "bg-status-blue-background text-status-blue-text",
		purple: "bg-status-purple-background text-status-purple-text",
		neutral: "bg-background-tertiary-default text-text-secondary",
		gray: "bg-background-secondary-default text-text-primary",
		soft: "bg-background-secondary-default text-text-secondary"
	}
});
function Jd({ variant: e = "bold", color: t = "neutral", className: n, ref: r, ...i }) {
	return /* @__PURE__ */ (0, x.jsx)("span", {
		ref: r,
		className: Gd(qd.base, qd.variant[e], qd.color[t], n),
		...i
	});
}
//#endregion
//#region src/api.ts
var Yd = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(r(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Xd = (e) => {
	if (!e || typeof e != "object") return "";
	let t = e;
	for (let e of [
		"message",
		"detail",
		"error"
	]) {
		let n = t[e];
		if (typeof n == "string" && n) return n;
	}
	return "";
}, Zd = (e) => r(e);
async function Qd(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Yd(Xd(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function $d(e, t, n = "POST", r) {
	let i = await fetch(e, {
		method: n,
		...r ? { signal: r } : {},
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json"
		},
		credentials: "same-origin",
		body: JSON.stringify(t)
	}), a = null;
	try {
		a = await i.json();
	} catch {}
	if (!i.ok) throw new Yd(Xd(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region src/react/components/empty-state.tsx
function ef({ icon: e, title: t, children: n }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "flex flex-col items-center gap-2 rounded-2xl border border-separator-border px-6 py-12 text-center",
		children: [
			/* @__PURE__ */ (0, x.jsx)(e, {
				"aria-hidden": !0,
				className: "size-6 text-text-tertiary"
			}),
			/* @__PURE__ */ (0, x.jsx)("h3", {
				className: "text-headline-medium text-text-primary",
				children: t
			}),
			/* @__PURE__ */ (0, x.jsx)("p", {
				className: "max-w-prose text-body-2-regular text-text-secondary",
				children: n
			})
		]
	});
}
//#endregion
//#region src/react/components/loading-dots.tsx
function tf({ label: e }) {
	return /* @__PURE__ */ (0, x.jsxs)("p", {
		role: "status",
		className: "flex items-center gap-2 text-caption-1-regular text-text-secondary",
		children: [/* @__PURE__ */ (0, x.jsxs)("span", {
			"aria-hidden": !0,
			className: "inline-flex items-center gap-1",
			children: [
				/* @__PURE__ */ (0, x.jsx)("i", { className: "dot-wave-0 size-1 rounded-full bg-current" }),
				/* @__PURE__ */ (0, x.jsx)("i", { className: "dot-wave-1 size-1 rounded-full bg-current" }),
				/* @__PURE__ */ (0, x.jsx)("i", { className: "dot-wave-2 size-1 rounded-full bg-current" })
			]
		}), e]
	});
}
//#endregion
//#region src/react/components/note.tsx
function nf({ tone: e, title: t, children: n }) {
	let r = /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [t ? /* @__PURE__ */ (0, x.jsx)("p", {
		className: "text-body-medium",
		children: t
	}) : null, /* @__PURE__ */ (0, x.jsx)("p", {
		className: "text-body-2-regular",
		children: n
	})] });
	switch (e) {
		case "info": return /* @__PURE__ */ (0, x.jsx)("div", {
			role: "status",
			className: "flex flex-col gap-0.5 rounded-2lg bg-notification-information-background px-3 py-2 text-notification-information-foreground",
			children: r
		});
		case "success": return /* @__PURE__ */ (0, x.jsx)("div", {
			role: "status",
			className: "flex flex-col gap-0.5 rounded-2lg bg-notification-success-background px-3 py-2 text-notification-success-foreground",
			children: r
		});
		case "warning": return /* @__PURE__ */ (0, x.jsx)("div", {
			role: "note",
			className: "flex flex-col gap-0.5 rounded-2lg bg-status-yellow-background px-3 py-2 text-status-yellow-text",
			children: r
		});
		case "error": return /* @__PURE__ */ (0, x.jsx)("div", {
			role: "alert",
			className: "flex flex-col gap-0.5 rounded-2lg bg-background-tertiary-error px-3 py-2 text-text-error-primary",
			children: r
		});
		default: return /* @__PURE__ */ (0, x.jsx)("div", {
			role: "note",
			className: "flex flex-col gap-0.5 rounded-2lg bg-background-tertiary-default px-3 py-2 text-text-secondary",
			children: r
		});
	}
}
//#endregion
//#region src/react/components/page.tsx
function rf({ children: e }) {
	return /* @__PURE__ */ (0, x.jsx)("div", {
		className: "mx-auto flex w-full max-w-board flex-col gap-8",
		children: e
	});
}
//#endregion
//#region src/react/components/progress.tsx
function af({ label: e, value: t, max: n = 100, stops: r = [] }) {
	let i = Math.min(Math.max(t, 0), n);
	return /* @__PURE__ */ (0, x.jsxs)("svg", {
		role: "progressbar",
		"aria-label": e,
		"aria-valuemin": 0,
		"aria-valuemax": n,
		"aria-valuenow": t,
		viewBox: `0 0 ${n} 1`,
		preserveAspectRatio: "none",
		className: "h-1.5 w-full overflow-hidden rounded-full",
		children: [
			/* @__PURE__ */ (0, x.jsx)("rect", {
				width: n,
				height: 1,
				className: "fill-background-tertiary-default"
			}),
			/* @__PURE__ */ (0, x.jsx)("rect", {
				width: i,
				height: 1,
				className: "fill-border-focus-ring"
			}),
			r.map((e) => /* @__PURE__ */ (0, x.jsx)("rect", {
				x: e,
				width: .4,
				height: 1,
				className: "fill-background-secondary-default"
			}, e))
		]
	});
}
//#endregion
//#region src/react/query.ts
var of = new Ke({ defaultOptions: { queries: {
	networkMode: "always",
	retry: 0,
	refetchOnWindowFocus: !1,
	refetchOnMount: !1,
	retryOnMount: !1
} } }), sf = "/api/tasks", cf = ["tasks"], lf = 2e3, uf = 1e4, df = (e) => e?.running.length ? lf : uf, ff = (e) => Qd(sf, e);
async function pf(e) {
	await of.fetchQuery({
		queryKey: cf,
		queryFn: () => ff(e)
	});
}
var mf = {
	manual: "手动",
	scheduled: "定时",
	startup: "启动",
	cli: "命令行"
}, hf = {
	pending: "排队中",
	running: "进行中",
	succeeded: "已完成",
	failed: "失败",
	cancelled: "已取消",
	interrupted: "被打断"
}, gf = (e) => hf[e] || e, _f = {
	checked: "已检查",
	total: "总数",
	scanned: "已扫描",
	identified: "已识别",
	candidates: "资料候选",
	covers: "封面",
	changed: "已改动",
	operation: "操作",
	ok: "取得",
	miss: "未取得",
	kept: "保留",
	planned: "计划",
	done: "已处理",
	added: "新增",
	written: "已写入",
	removed: "已移除",
	exit_code: "退出码",
	issue_count: "问题"
};
function vf(e) {
	if (typeof e != "number" || !Number.isFinite(e) || e < 0) return "";
	let t = Math.floor(e);
	if (t < 60) return `${t} 秒`;
	let n = Math.floor(t / 60);
	return n < 60 ? `${n} 分 ${t % 60} 秒` : `${Math.floor(n / 60)} 小时 ${n % 60} 分`;
}
function yf(e) {
	if (!e) return "";
	let t = new Date(e);
	return Number.isNaN(t.getTime()) ? "" : t.toLocaleString(void 0, {
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit"
	});
}
function bf(e) {
	return Object.entries(e || {}).filter(([e, t]) => e !== "blocked_by" && (typeof t == "number" || typeof t == "string") && String(t) !== "").map(([e, t]) => `${_f[e] || e} ${t}`).join(" · ");
}
//#endregion
//#region src/react/activity/activity-page.tsx
var xf = {
	succeeded: "lime",
	failed: "rose",
	cancelled: "yellow",
	interrupted: "yellow"
};
function Sf({ status: e }) {
	return /* @__PURE__ */ (0, x.jsx)(Jd, {
		color: xf[e] ?? "neutral",
		children: gf(e)
	});
}
function Cf({ run: e, meta: t, children: n, footer: r }) {
	return /* @__PURE__ */ (0, x.jsxs)("li", {
		"data-status": e.status,
		"data-task-key": e.task_key,
		className: e.status === "failed" ? "flex flex-col rounded-2xl border border-border-error-default" : "flex flex-col rounded-2xl border border-separator-border",
		children: [/* @__PURE__ */ (0, x.jsxs)("div", {
			className: "flex flex-col gap-1.5 px-5 pt-5 pb-4",
			children: [
				/* @__PURE__ */ (0, x.jsxs)("div", {
					className: "flex flex-wrap items-center gap-2",
					children: [/* @__PURE__ */ (0, x.jsx)("strong", {
						className: "min-w-0 break-words text-title-1-medium text-text-primary",
						children: e.task_label
					}), /* @__PURE__ */ (0, x.jsx)(Sf, { status: e.status })]
				}),
				/* @__PURE__ */ (0, x.jsx)("p", {
					className: "text-caption-1-regular text-text-secondary",
					children: t
				}),
				n
			]
		}), r ? /* @__PURE__ */ (0, x.jsx)("div", {
			className: "border-t border-separator-border px-5 py-3",
			children: /* @__PURE__ */ (0, x.jsx)("p", {
				className: "text-caption-1-regular text-text-secondary",
				children: r
			})
		}) : null]
	});
}
function wf({ run: e }) {
	let t = e.progress_total || 0, n = e.progress_current || 0, r = e.progress_label || "正在进行", i = vf(e.elapsed_seconds), a = [mf[e.trigger] || e.trigger, i && `已跑 ${i}`].filter(Boolean).join(" · ");
	return /* @__PURE__ */ (0, x.jsx)(Cf, {
		run: e,
		meta: a,
		children: t > 0 ? /* @__PURE__ */ (0, x.jsxs)("div", {
			className: "flex flex-col gap-1.5",
			children: [/* @__PURE__ */ (0, x.jsx)(af, {
				label: r,
				value: n,
				max: t
			}), /* @__PURE__ */ (0, x.jsxs)("p", {
				className: "text-caption-1-regular text-text-secondary",
				children: [
					r,
					" · ",
					n,
					" / ",
					t,
					" 项"
				]
			})]
		}) : /* @__PURE__ */ (0, x.jsx)(tf, { label: r })
	});
}
function Tf({ run: e }) {
	let t = bf(e.result_summary), n = vf(e.elapsed_seconds), r = [
		mf[e.trigger] || e.trigger,
		yf(e.finished_at),
		n && `用时 ${n}`
	].filter(Boolean).join(" · ");
	return /* @__PURE__ */ (0, x.jsx)(Cf, {
		run: e,
		meta: r,
		footer: e.error,
		children: t ? /* @__PURE__ */ (0, x.jsx)("p", {
			className: "text-caption-1-regular text-text-secondary",
			children: t
		}) : null
	});
}
function Ef({ title: e, children: t }) {
	let n = (0, b.useId)();
	return /* @__PURE__ */ (0, x.jsxs)("section", {
		"aria-labelledby": n,
		className: "flex min-w-0 flex-col gap-3",
		children: [/* @__PURE__ */ (0, x.jsx)("h3", {
			id: n,
			className: "text-title-2-semibold text-text-primary",
			children: e
		}), t]
	});
}
function Df({ live: e = !1, children: t }) {
	return /* @__PURE__ */ (0, x.jsx)("ul", {
		"aria-live": e ? "polite" : void 0,
		className: "flex min-w-0 flex-col gap-3",
		children: t
	});
}
function Of(e) {
	let t = at({
		queryKey: cf,
		queryFn: ({ signal: e }) => ff(e),
		refetchInterval: (e) => df(e.state.data)
	}), n = t.data, r = t.error ? Zd(t.error) : "";
	if (!n) return /* @__PURE__ */ (0, x.jsx)(rf, { children: /* @__PURE__ */ (0, x.jsx)(nf, {
		tone: "error",
		children: r || "读取任务中心失败"
	}) });
	let i = n.running || [], a = n.skipped || [], o = (n.finished || []).filter((e) => !a.some((t) => t.id === e.id)), s = !i.length && !a.length && !o.length;
	return /* @__PURE__ */ (0, x.jsxs)(rf, { children: [
		r ? /* @__PURE__ */ (0, x.jsx)(nf, {
			tone: "error",
			children: r
		}) : null,
		n.available === !1 ? /* @__PURE__ */ (0, x.jsx)(nf, {
			tone: "warning",
			children: n.message || "账本上还没有任务中心的表"
		}) : null,
		s ? /* @__PURE__ */ (0, x.jsx)(ef, {
			icon: fu,
			title: "还没有任务记录",
			children: "扫描、追更检查、批量操作和命令行批处理跑起来之后，这里会显示它们的进度与结果。"
		}) : /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [
			/* @__PURE__ */ (0, x.jsx)(Ef, {
				title: "正在进行",
				children: i.length ? /* @__PURE__ */ (0, x.jsx)(Df, {
					live: !0,
					children: i.map((e) => /* @__PURE__ */ (0, x.jsx)(wf, { run: e }, e.id))
				}) : /* @__PURE__ */ (0, x.jsx)("p", {
					className: "text-body-2-regular text-text-secondary",
					children: "没有任务在跑。"
				})
			}),
			a.length ? /* @__PURE__ */ (0, x.jsx)(Ef, {
				title: "被挡下的",
				children: /* @__PURE__ */ (0, x.jsx)(Df, { children: a.map((e) => /* @__PURE__ */ (0, x.jsx)(Tf, { run: e }, e.id)) })
			}) : null,
			o.length ? /* @__PURE__ */ (0, x.jsx)(Ef, {
				title: "最近完成",
				children: /* @__PURE__ */ (0, x.jsx)(Df, { children: o.map((e) => /* @__PURE__ */ (0, x.jsx)(Tf, { run: e }, e.id)) })
			}) : null
		] })
	] });
}
//#endregion
//#region src/react/boardui/components/base/buttons/button.tsx
var kf = Kd({
	base: [
		"inline-flex items-center justify-center gap-0.5 whitespace-nowrap overflow-hidden",
		"font-sans select-none cursor-pointer",
		"button-press-motion",
		"outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus-ring",
		"disabled:cursor-not-allowed aria-disabled:cursor-not-allowed"
	].join(" "),
	size: {
		medium: "h-9 rounded-2lg p-2 text-body-medium",
		small: "h-8 rounded-lg px-2 py-1.5 text-body-medium",
		xs: "h-6 rounded-sm px-2 text-caption-1-semibold"
	},
	iconOnlySize: {
		medium: "",
		small: "size-8 p-0",
		xs: "size-6 p-0"
	},
	icon: {
		medium: "size-5 shrink-0",
		small: "size-[18px] shrink-0",
		xs: "size-3.5 shrink-0"
	},
	label: {
		medium: "inline-flex items-center justify-center px-1 shrink-0",
		small: "inline-flex items-center justify-center px-0.5 shrink-0",
		xs: "inline-flex items-center justify-center px-0.5 shrink-0"
	},
	variant: {
		primary: [
			"bg-button-primary text-text-white shadow-xs",
			"disabled:text-button-primary-disabled-foreground disabled:shadow-none",
			"aria-disabled:text-button-primary-disabled-foreground aria-disabled:shadow-none"
		].join(" "),
		danger: [
			"bg-button-danger text-text-white shadow-xs",
			"disabled:text-foreground-disabled-danger disabled:shadow-none",
			"aria-disabled:text-foreground-disabled-danger aria-disabled:shadow-none"
		].join(" "),
		secondary: [
			"bg-background-primary-default text-text-primary",
			"border border-border-button-default shadow-xs",
			"hover:bg-background-primary-hover  hover:border-border-button-hover",
			"active:bg-background-primary-active active:border-border-button-active",
			"disabled:bg-background-primary-disabled disabled:border-border-button-default disabled:text-text-tertiary disabled:shadow-none",
			"aria-disabled:bg-background-primary-disabled aria-disabled:border-border-button-default aria-disabled:text-text-tertiary aria-disabled:shadow-none"
		].join(" "),
		ghost: [
			"bg-button-ghost-background text-button-ghost-foreground",
			"hover:bg-button-ghost-hover active:bg-button-ghost-active",
			"disabled:bg-button-ghost-disabled disabled:text-button-ghost-disabled-foreground disabled:shadow-none",
			"aria-disabled:bg-button-ghost-disabled aria-disabled:text-button-ghost-disabled-foreground aria-disabled:shadow-none"
		].join(" ")
	}
});
function Af({ variant: e = "primary", size: t = "medium", iconOnly: n = !1, leadingIcon: r, trailingIcon: i, children: a, className: o, type: s = "button", ref: c, ...l }) {
	return /* @__PURE__ */ (0, x.jsxs)("button", {
		ref: c,
		type: s,
		className: Gd(kf.base, kf.size[t], kf.variant[e], n && kf.iconOnlySize[t], o),
		...l,
		children: [
			r ? /* @__PURE__ */ (0, x.jsx)(r, {
				className: kf.icon[t],
				"aria-hidden": !0
			}) : null,
			!n && a != null && /* @__PURE__ */ (0, x.jsx)("span", {
				className: kf.label[t],
				children: a
			}),
			!n && i ? /* @__PURE__ */ (0, x.jsx)(i, {
				className: kf.icon[t],
				"aria-hidden": !0
			}) : null
		]
	});
}
//#endregion
//#region src/react/quality-goals/quality-goals.ts
var jf = "/api/quality-goals?limit=200", Mf = ["quality-goals"], Nf = (e) => Qd(jf, e);
async function Pf(e) {
	await of.fetchQuery({
		queryKey: Mf,
		queryFn: () => Nf(e)
	});
}
var Ff = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
//#endregion
//#region src/react/quality-goals/quality-goals-page.tsx
function If({ item: r, openItem: i, javTitleHtml: a, javDisplayName: o, srcBadge: s }) {
	let c = () => i(r.id);
	return /* @__PURE__ */ (0, x.jsxs)("li", {
		"data-goal-id": r.id,
		className: "flex min-w-0 flex-col gap-3 rounded-2xl border border-separator-border p-3",
		children: [/* @__PURE__ */ (0, x.jsxs)("div", {
			className: "flex min-w-0 gap-4",
			children: [/* @__PURE__ */ (0, x.jsxs)("button", {
				type: "button",
				onClick: c,
				"aria-label": `打开 ${o(r)}`,
				className: "relative inline-grid w-card-cover shrink-0 aspect-card-cover cursor-pointer place-items-center overflow-hidden rounded-lg bg-black",
				children: [/* @__PURE__ */ (0, x.jsx)("span", {
					className: "text-caption-1-regular text-text-tertiary",
					children: "暂无预览"
				}), /* @__PURE__ */ (0, x.jsx)("img", {
					src: Ff(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove(),
					className: "absolute inset-0 size-full object-contain"
				})]
			}), /* @__PURE__ */ (0, x.jsxs)("div", {
				className: "flex min-w-0 flex-col gap-1.5",
				children: [
					/* @__PURE__ */ (0, x.jsx)("h3", {
						className: "text-title-1-medium text-text-primary",
						children: /* @__PURE__ */ (0, x.jsx)("button", {
							type: "button",
							"data-middle-truncate": !0,
							onClick: c,
							className: "block w-full cursor-pointer text-left",
							dangerouslySetInnerHTML: { __html: a(r) }
						})
					}),
					/* @__PURE__ */ (0, x.jsxs)("p", {
						className: "flex flex-wrap items-center gap-2 text-caption-1-regular text-text-secondary",
						children: [
							/* @__PURE__ */ (0, x.jsx)("span", {
								className: "contents",
								dangerouslySetInnerHTML: { __html: s(r.location, r.cost) }
							}),
							/* @__PURE__ */ (0, x.jsx)("span", { children: e[r.location] ?? r.location }),
							/* @__PURE__ */ (0, x.jsx)("span", { children: t(r.duration) }),
							/* @__PURE__ */ (0, x.jsx)("span", { children: n(r.size ?? 0) })
						]
					}),
					r.reason ? /* @__PURE__ */ (0, x.jsx)("p", {
						className: "text-caption-1-regular text-text-secondary",
						children: r.reason
					}) : null
				]
			})]
		}), /* @__PURE__ */ (0, x.jsx)("footer", {
			className: "flex justify-end",
			children: /* @__PURE__ */ (0, x.jsx)(Af, {
				variant: "secondary",
				size: "small",
				onClick: c,
				children: "查看版本"
			})
		})]
	});
}
function Lf(e) {
	let t = at({
		queryKey: Mf,
		queryFn: ({ signal: e }) => Nf(e)
	}), n = t.data;
	if (!n) return /* @__PURE__ */ (0, x.jsx)(rf, { children: /* @__PURE__ */ (0, x.jsx)(nf, {
		tone: "error",
		title: "读取失败",
		children: t.error ? Zd(t.error) : "读取高清版目标失败"
	}) });
	let r = n.items || [];
	return r.length ? /* @__PURE__ */ (0, x.jsxs)(rf, { children: [/* @__PURE__ */ (0, x.jsxs)("p", {
		className: "text-body-2-regular text-text-secondary",
		children: [
			/* @__PURE__ */ (0, x.jsx)("strong", {
				className: "text-title-2-semibold text-text-primary",
				children: "待升级"
			}),
			" · ",
			n.total,
			" 部作品"
		]
	}), /* @__PURE__ */ (0, x.jsx)("ul", {
		className: "card-grid gap-5",
		children: r.map((t) => /* @__PURE__ */ (0, x.jsx)(If, {
			item: t,
			...e
		}, t.id))
	})] }) : /* @__PURE__ */ (0, x.jsx)(rf, { children: /* @__PURE__ */ (0, x.jsx)(ef, {
		icon: mu,
		title: "没有标记中的高清版目标",
		children: "现有版本都已满足条件，或还没有加入追踪。"
	}) });
}
//#endregion
//#region src/react/boardui/components/application/settings/settings-rows.tsx
function Rf({ className: e, children: t }) {
	return /* @__PURE__ */ (0, x.jsx)("div", {
		className: Gd("flex w-full flex-col rounded-2xl bg-background-secondary-default pl-3", e),
		children: t
	});
}
function zf({ className: e, children: t }) {
	return /* @__PURE__ */ (0, x.jsx)("p", {
		className: Gd("w-full px-3 text-body-2-medium text-text-secondary", e),
		children: t
	});
}
function Bf({ label: e, description: t, children: n }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: Gd("flex min-h-[52px] w-full items-center justify-between gap-4 py-2.5 pr-2.5", "border-b border-separator-border last:border-b-0"),
		children: [/* @__PURE__ */ (0, x.jsxs)("div", {
			className: "flex min-w-0 flex-col",
			children: [/* @__PURE__ */ (0, x.jsx)("p", {
				className: "text-body-regular text-text-primary",
				children: e
			}), t && /* @__PURE__ */ (0, x.jsx)("p", {
				className: "text-body-2-regular text-text-secondary",
				children: t
			})]
		}), n]
	});
}
//#endregion
//#region node_modules/react-aria-components/dist/private/utils.mjs
var $ = Symbol("default");
function Vf({ values: e, children: t }) {
	for (let [n, r] of e) t = /*#__PURE__*/ b.createElement(n.Provider, { value: r }, t);
	return t;
}
function Hf(e) {
	let { className: t, style: n, children: r, defaultClassName: i, defaultChildren: a, defaultStyle: o, values: s, render: c } = e;
	return (0, b.useMemo)(() => {
		let e, l, u;
		return e = typeof t == "function" ? t({
			...s,
			defaultClassName: i
		}) : t, l = typeof n == "function" ? n({
			...s,
			defaultStyle: o || {}
		}) : n, u = typeof r == "function" ? r({
			...s,
			defaultChildren: a
		}) : r ?? a, {
			className: e ?? i,
			style: l || o ? {
				...o,
				...l
			} : void 0,
			children: u ?? a,
			"data-rac": "",
			render: c ? (e) => c(e, s) : void 0
		};
	}, [
		t,
		n,
		r,
		i,
		a,
		o,
		s,
		c
	]);
}
function Uf(e, t) {
	let n = (0, b.useContext)(e);
	if (t === null) return null;
	if (n && typeof n == "object" && "slots" in n && n.slots) {
		let e = t || $;
		if (!n.slots[e]) {
			let e = new Intl.ListFormat().format(Object.keys(n.slots).map((e) => `"${e}"`)), r = t ? `Invalid slot "${t}".` : "A slot prop is required.";
			throw Error(`${r} Valid slot names are ${e}.`);
		}
		return n.slots[e];
	}
	return n;
}
function Wf(e, t, n) {
	let { ref: r, ...i } = Uf(n, e.slot) || {}, a = kr((0, b.useMemo)(() => ur(t, r), [t, r])), o = U(i, e);
	return "style" in i && i.style && "style" in e && e.style && (o.style = typeof i.style == "function" || typeof e.style == "function" ? (t) => {
		let n = typeof i.style == "function" ? i.style(t) : i.style, r = {
			...t.defaultStyle,
			...n
		}, a = typeof e.style == "function" ? e.style({
			...t,
			defaultStyle: r
		}) : e.style;
		return {
			...r,
			...a
		};
	} : {
		...i.style,
		...e.style
	}), [o, a];
}
function Gf(e = !0) {
	let [t, n] = (0, b.useState)(e), r = (0, b.useRef)(!1), i = (0, b.useCallback)((e) => {
		r.current = !0, n(!!e);
	}, []);
	return H(() => {
		r.current || n(!1);
	}, []), [i, t];
}
function Kf(e) {
	let t = /^(data-.*)$/, n = {};
	for (let r in e) t.test(r) || (n[r] = e[r]);
	return n;
}
function qf(e, t, n) {
	let { render: r, ...i } = t, a = (0, b.useRef)(null), o = (0, b.useMemo)(() => ur(n, a), [n, a]);
	H(() => {}, [e, r]);
	let s = {
		...i,
		ref: o
	};
	return r ? r(s, void 0) : /*#__PURE__*/ b.createElement(e, s);
}
var Jf = {}, Yf = new Proxy({}, { get(e, t) {
	if (typeof t != "string") return;
	let n = Jf[t];
	return n || (n = /*#__PURE__*/ (0, b.forwardRef)(qf.bind(null, t)), Jf[t] = n), n;
} }), Xf = /*#__PURE__*/ (0, b.createContext)(null), Zf = /*#__PURE__*/ (0, b.createContext)(null), Qf = /*#__PURE__*/ (0, b.createContext)(null), $f = {
	CollectionRoot({ collection: e, renderDropIndicator: t }) {
		return ep(e, null, t);
	},
	CollectionBranch({ collection: e, parent: t, renderDropIndicator: n }) {
		return ep(e, t, n);
	}
};
function ep(e, t, n) {
	return ht({
		items: t ? e.getChildren(t.key) : e,
		dependencies: [n],
		children(t) {
			if (t.type === "content") return /*#__PURE__*/ b.createElement(b.Fragment, null);
			let r = t.render(t);
			return !n || t.type !== "item" ? r : /*#__PURE__*/ b.createElement(b.Fragment, null, n({
				type: "item",
				key: t.key,
				dropPosition: "before"
			}), r, tp(e, t, n));
		}
	});
}
function tp(e, t, n) {
	let r = t.key, i = e.getKeyAfter(r), a = i == null ? null : e.getItem(i);
	for (; a != null && a.type !== "item";) i = e.getKeyAfter(a.key), a = i == null ? null : e.getItem(i);
	let o = t.nextKey == null ? null : e.getItem(t.nextKey);
	for (; o != null && o.type !== "item";) o = o.nextKey == null ? null : e.getItem(o.nextKey);
	let s = [];
	if (o == null) {
		let r = t;
		for (; r?.type === "item" && (!a || r.parentKey !== a.parentKey && a.level < r.level);) {
			let t = n({
				type: "item",
				key: r.key,
				dropPosition: "after"
			});
			/*#__PURE__*/ (0, b.isValidElement)(t) && s.push(/*#__PURE__*/ (0, b.cloneElement)(t, { key: `${r.key}-after` })), r = r.parentKey == null ? null : e.getItem(r.parentKey);
		}
	}
	return s;
}
var np = /*#__PURE__*/ (0, b.createContext)($f), rp = /*#__PURE__*/ (0, b.createContext)({}), ip = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, rp);
	let { elementType: n = "label", ...r } = e, i = Yf[n];
	return /*#__PURE__*/ b.createElement(i, {
		className: "react-aria-Label",
		...r,
		ref: t
	});
}), ap = /*#__PURE__*/ (0, b.createContext)(null), op = /*#__PURE__*/ (0, b.createContext)({}), sp = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, op);
	let n = e, { isPending: r } = n, { buttonProps: i, isPressed: a } = va(e, t);
	i = lp(i, r);
	let { focusProps: o, isFocused: s, isFocusVisible: c } = pc(e), { hoverProps: l, isHovered: u } = bc({
		...e,
		isDisabled: e.isDisabled || r
	}), d = {
		isHovered: u,
		isPressed: (n.isPressed || a) && !r,
		isFocused: s,
		isFocusVisible: c,
		isDisabled: e.isDisabled || !1,
		isPending: r ?? !1
	}, f = Hf({
		...e,
		values: d,
		defaultClassName: "react-aria-Button"
	}), p = sr(i.id), m = sr(), h = i["aria-labelledby"];
	r && (h ? h = `${h} ${m}` : i["aria-label"] && (h = `${p} ${m}`));
	let g = (0, b.useRef)(r);
	(0, b.useEffect)(() => {
		let e = { "aria-labelledby": h || p };
		(!g.current && s && r || g.current && s && !r) && Xa(e, "assertive"), g.current = r;
	}, [
		r,
		s,
		h,
		p
	]);
	let _ = Yi(e, { global: !0 });
	return delete _.onClick, /*#__PURE__*/ b.createElement(Yf.button, {
		...U(_, f, i, o, l),
		type: i.type === "submit" && r ? "button" : i.type,
		id: p,
		ref: t,
		"aria-labelledby": h,
		slot: e.slot || void 0,
		"aria-disabled": r ? "true" : i["aria-disabled"],
		"data-disabled": e.isDisabled || void 0,
		"data-pressed": d.isPressed || void 0,
		"data-hovered": u || void 0,
		"data-focused": s || void 0,
		"data-pending": r || void 0,
		"data-focus-visible": c || void 0
	}, /*#__PURE__*/ b.createElement(ap.Provider, { value: { id: m } }, f.children));
}), cp = /Focus|Blur|Hover|Pointer(Enter|Leave|Over|Out)|Mouse(Enter|Leave|Over|Out)/;
function lp(e, t) {
	if (t) {
		for (let t in e) t.startsWith("on") && !cp.test(t) && (e[t] = void 0);
		e.href = void 0, e.target = void 0;
	}
	return e;
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Heading.mjs
var up = /*#__PURE__*/ (0, b.createContext)({}), dp = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	[e, t] = Wf(e, t, up);
	let { children: n, level: r = 3, className: i, ...a } = e, o = Yf[`h${r}`];
	return /*#__PURE__*/ b.createElement(o, {
		...a,
		ref: t,
		className: i ?? "react-aria-Heading"
	}, n);
}), fp = /*#__PURE__*/ (0, b.createContext)({}), pp = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, fp);
	let { elementType: n = "span", ...r } = e, i = Yf[n];
	return /*#__PURE__*/ b.createElement(i, {
		className: "react-aria-Text",
		...r,
		ref: t
	});
}), mp = /*#__PURE__*/ (0, b.createContext)(null), hp = /*#__PURE__*/ (0, b.createContext)(null), gp = /*#__PURE__*/ (0, b.createContext)(null), _p = /*#__PURE__*/ (0, b.createContext)(null), vp = /*#__PURE__*/ (0, b.createContext)(null);
function yp(e, t) {
	let { validationBehavior: n } = Uf(hp) || {}, r = e.validationBehavior ?? n ?? "native", i = (0, b.useContext)(_p), a = kr((0, b.useMemo)(() => ur(t, e.inputRef === void 0 ? null : e.inputRef), [t, e.inputRef])), o = {
		...Kf(e),
		children: typeof e.children == "function" || e.children,
		value: e.value,
		validationBehavior: r
	};
	return [i ? Fo(o, i, a) : Do(o, Po(e), a), a];
}
var bp = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { inputRef: n = null, ...r } = e;
	[e, t] = Wf(r, t, gp);
	let [i, a] = yp(e, n);
	return /*#__PURE__*/ b.createElement(vp.Provider, { value: {
		...i,
		inputRef: a,
		defaultClassName: "react-aria-Checkbox",
		isIndeterminate: e.isIndeterminate,
		isRequired: e.isRequired
	} }, /*#__PURE__*/ b.createElement(xp, {
		...e,
		ref: t
	}));
}), xp = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { labelProps: n, inputProps: r, isSelected: i, isDisabled: a, isReadOnly: o, isPressed: s, isInvalid: c, inputRef: l, defaultClassName: u, isIndeterminate: d, isRequired: f } = (0, b.useContext)(vp), { isFocused: p, isFocusVisible: m, focusProps: h } = pc(), g = a || o, { hoverProps: _, isHovered: v } = bc({
		...e,
		isDisabled: g
	}), y = Hf({
		...e,
		defaultClassName: u,
		values: {
			isSelected: i,
			isIndeterminate: d || !1,
			isPressed: s,
			isHovered: v,
			isFocused: p,
			isFocusVisible: m,
			isDisabled: a,
			isReadOnly: o,
			isInvalid: c,
			isRequired: f || !1
		}
	}), x = Yi(e, { global: !0 });
	return delete x.id, delete x.onClick, /*#__PURE__*/ b.createElement(Yf.label, {
		...U(x, n, _, y),
		ref: t,
		slot: e.slot || void 0,
		"data-selected": i || void 0,
		"data-indeterminate": d || void 0,
		"data-pressed": s || void 0,
		"data-hovered": v || void 0,
		"data-focused": p || void 0,
		"data-focus-visible": m || void 0,
		"data-disabled": a || void 0,
		"data-readonly": o || void 0,
		"data-invalid": c || void 0,
		"data-required": f || void 0
	}, /*#__PURE__*/ b.createElement(Ro, { elementType: "span" }, /*#__PURE__*/ b.createElement("input", {
		...U(r, h),
		ref: l
	})), y.children);
}), Sp = /*#__PURE__*/ (0, b.createContext)({}), Cp = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	[e, t] = Wf(e, t, Sp);
	let { isDisabled: n, isInvalid: r, isReadOnly: i, onHoverStart: a, onHoverChange: o, onHoverEnd: s, ...c } = e;
	n ??= !!e["aria-disabled"] && e["aria-disabled"] !== "false", r ??= !!e["aria-invalid"] && e["aria-invalid"] !== "false";
	let { hoverProps: l, isHovered: u } = bc({
		onHoverStart: a,
		onHoverChange: o,
		onHoverEnd: s,
		isDisabled: n
	}), { isFocused: d, isFocusVisible: f, focusProps: p } = pc({ within: !0 }), m = Hf({
		...e,
		values: {
			isHovered: u,
			isFocusWithin: d,
			isFocusVisible: f,
			isDisabled: n,
			isInvalid: r
		},
		defaultClassName: "react-aria-Group"
	});
	return /*#__PURE__*/ b.createElement(Yf.div, {
		...U(c, p, l),
		...m,
		ref: t,
		role: e.role ?? "group",
		slot: e.slot ?? void 0,
		"data-focus-within": d || void 0,
		"data-hovered": u || void 0,
		"data-focus-visible": f || void 0,
		"data-disabled": n || void 0,
		"data-invalid": r || void 0,
		"data-readonly": i || void 0
	}, m.children);
}), wp = /*#__PURE__*/ (0, b.createContext)({}), Tp = (e) => {
	let { onHoverStart: t, onHoverChange: n, onHoverEnd: r, ...i } = e;
	return i;
}, Ep = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, wp);
	let { hoverProps: n, isHovered: r } = bc({
		...e,
		isDisabled: e.disabled
	}), { isFocused: i, isFocusVisible: a, focusProps: o } = pc({
		isTextInput: !0,
		autoFocus: e.autoFocus
	}), s = !!e["aria-invalid"] && e["aria-invalid"] !== "false", c = Hf({
		...e,
		values: {
			isHovered: r,
			isFocused: i,
			isFocusVisible: a,
			isDisabled: e.disabled || !1,
			isInvalid: s
		},
		defaultClassName: "react-aria-Input"
	});
	return /*#__PURE__*/ b.createElement(Yf.input, {
		...U(Tp(e), o, n),
		...c,
		ref: t,
		"data-focused": i || void 0,
		"data-disabled": e.disabled || void 0,
		"data-hovered": r || void 0,
		"data-focus-visible": a || void 0,
		"data-invalid": s || void 0
	});
}), Dp = {};
Dp = {
	colorSwatchPicker: "تغييرات الألوان",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "حدد عنصرًا",
	tableResizer: "أداة تغيير الحجم"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/bg-BG.mjs
var Op = {};
Op = {
	colorSwatchPicker: "Цветови мостри",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Изберете предмет",
	tableResizer: "Преоразмерител"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/cs-CZ.mjs
var kp = {};
kp = {
	colorSwatchPicker: "Vzorky barev",
	dropzoneLabel: "Místo pro přetažení",
	selectPlaceholder: "Vyberte položku",
	tableResizer: "Změna velikosti"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/da-DK.mjs
var Ap = {};
Ap = {
	colorSwatchPicker: "Farveprøver",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Vælg et element",
	tableResizer: "Størrelsesændring"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/de-DE.mjs
var jp = {};
jp = {
	colorSwatchPicker: "Farbfelder",
	dropzoneLabel: "Ablegebereich",
	selectPlaceholder: "Element wählen",
	tableResizer: "Größenanpassung"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/el-GR.mjs
var Mp = {};
Mp = {
	colorSwatchPicker: "Χρωματικά δείγματα",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Επιλέξτε ένα αντικείμενο",
	tableResizer: "Αλλαγή μεγέθους"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/en-US.mjs
var Np = {};
Np = {
	selectPlaceholder: "Select an item",
	tableResizer: "Resizer",
	dropzoneLabel: "DropZone",
	colorSwatchPicker: "Color swatches"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/es-ES.mjs
var Pp = {};
Pp = {
	colorSwatchPicker: "Muestras de colores",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Seleccionar un artículo",
	tableResizer: "Cambiador de tamaño"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/et-EE.mjs
var Fp = {};
Fp = {
	colorSwatchPicker: "Värvinäidised",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Valige üksus",
	tableResizer: "Suuruse muutja"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/fi-FI.mjs
var Ip = {};
Ip = {
	colorSwatchPicker: "Värimallit",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Valitse kohde",
	tableResizer: "Koon muuttaja"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/fr-FR.mjs
var Lp = {};
Lp = {
	colorSwatchPicker: "Échantillons de couleurs",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Sélectionner un élément",
	tableResizer: "Redimensionneur"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/he-IL.mjs
var Rp = {};
Rp = {
	colorSwatchPicker: "דוגמיות צבע",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "בחר פריט",
	tableResizer: "שינוי גודל"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/hr-HR.mjs
var zp = {};
zp = {
	colorSwatchPicker: "Uzorci boja",
	dropzoneLabel: "Zona spuštanja",
	selectPlaceholder: "Odaberite stavku",
	tableResizer: "Promjena veličine"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/hu-HU.mjs
var Bp = {};
Bp = {
	colorSwatchPicker: "Színtárak",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Válasszon ki egy elemet",
	tableResizer: "Átméretező"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/it-IT.mjs
var Vp = {};
Vp = {
	colorSwatchPicker: "Campioni di colore",
	dropzoneLabel: "Zona di rilascio",
	selectPlaceholder: "Seleziona un elemento",
	tableResizer: "Ridimensionamento"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ja-JP.mjs
var Hp = {};
Hp = {
	colorSwatchPicker: "カラースウォッチ",
	dropzoneLabel: "ドロップゾーン",
	selectPlaceholder: "項目を選択",
	tableResizer: "サイズ変更ツール"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ko-KR.mjs
var Up = {};
Up = {
	colorSwatchPicker: "색상 견본",
	dropzoneLabel: "드롭 영역",
	selectPlaceholder: "항목 선택",
	tableResizer: "크기 조정기"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/lt-LT.mjs
var Wp = {};
Wp = {
	colorSwatchPicker: "Spalvų pavyzdžiai",
	dropzoneLabel: "„DropZone“",
	selectPlaceholder: "Pasirinkite elementą",
	tableResizer: "Dydžio keitiklis"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/lv-LV.mjs
var Gp = {};
Gp = {
	colorSwatchPicker: "Krāsu paraugi",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Izvēlēties vienumu",
	tableResizer: "Izmēra mainītājs"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/nb-NO.mjs
var Kp = {};
Kp = {
	colorSwatchPicker: "Fargekart",
	dropzoneLabel: "Droppsone",
	selectPlaceholder: "Velg et element",
	tableResizer: "Størrelsesendrer"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/nl-NL.mjs
var qp = {};
qp = {
	colorSwatchPicker: "kleurstalen",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Selecteer een item",
	tableResizer: "Resizer"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/pl-PL.mjs
var Jp = {};
Jp = {
	colorSwatchPicker: "Próbki kolorów",
	dropzoneLabel: "Strefa upuszczania",
	selectPlaceholder: "Wybierz element",
	tableResizer: "Zmiana rozmiaru"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/pt-BR.mjs
var Yp = {};
Yp = {
	colorSwatchPicker: "Amostras de cores",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Selecione um item",
	tableResizer: "Redimensionador"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/pt-PT.mjs
var Xp = {};
Xp = {
	colorSwatchPicker: "Amostras de cores",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Selecione um item",
	tableResizer: "Redimensionador"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ro-RO.mjs
var Zp = {};
Zp = {
	colorSwatchPicker: "Specimene de culoare",
	dropzoneLabel: "Zonă de plasare",
	selectPlaceholder: "Selectați un element",
	tableResizer: "Instrument de redimensionare"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ru-RU.mjs
var Qp = {};
Qp = {
	colorSwatchPicker: "Цветовые образцы",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Выберите элемент",
	tableResizer: "Средство изменения размера"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sk-SK.mjs
var $p = {};
$p = {
	colorSwatchPicker: "Vzorkovníky farieb",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Vyberte položku",
	tableResizer: "Nástroj na zmenu veľkosti"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sl-SI.mjs
var em = {};
em = {
	colorSwatchPicker: "Barvne palete",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Izberite element",
	tableResizer: "Spreminjanje velikosti"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sr-SP.mjs
var tm = {};
tm = {
	colorSwatchPicker: "Uzorci boje",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Izaberite stavku",
	tableResizer: "Promena veličine"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sv-SE.mjs
var nm = {};
nm = {
	colorSwatchPicker: "Färgrutor",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Välj en artikel",
	tableResizer: "Storleksändrare"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/tr-TR.mjs
var rm = {};
rm = {
	colorSwatchPicker: "Renk örnekleri",
	dropzoneLabel: "Bırakma Bölgesi",
	selectPlaceholder: "Bir öğe seçin",
	tableResizer: "Yeniden boyutlandırıcı"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/uk-UA.mjs
var im = {};
im = {
	colorSwatchPicker: "Зразки кольорів",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Виберіть елемент",
	tableResizer: "Засіб змінення розміру"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/zh-CN.mjs
var am = {};
am = {
	colorSwatchPicker: "颜色色板",
	dropzoneLabel: "放置区域",
	selectPlaceholder: "选择一个项目",
	tableResizer: "尺寸调整器"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/zh-TW.mjs
var om = {};
om = {
	colorSwatchPicker: "色票",
	dropzoneLabel: "放置區",
	selectPlaceholder: "選取項目",
	tableResizer: "大小調整器"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intlStrings.mjs
var sm = {};
sm = {
	"ar-AE": Dp,
	"bg-BG": Op,
	"cs-CZ": kp,
	"da-DK": Ap,
	"de-DE": jp,
	"el-GR": Mp,
	"en-US": Np,
	"es-ES": Pp,
	"et-EE": Fp,
	"fi-FI": Ip,
	"fr-FR": Lp,
	"he-IL": Rp,
	"hr-HR": zp,
	"hu-HU": Bp,
	"it-IT": Vp,
	"ja-JP": Hp,
	"ko-KR": Up,
	"lt-LT": Wp,
	"lv-LV": Gp,
	"nb-NO": Kp,
	"nl-NL": qp,
	"pl-PL": Jp,
	"pt-BR": Yp,
	"pt-PT": Xp,
	"ro-RO": Zp,
	"ru-RU": Qp,
	"sk-SK": $p,
	"sl-SI": em,
	"sr-SP": tm,
	"sv-SE": nm,
	"tr-TR": rm,
	"uk-UA": im,
	"zh-CN": am,
	"zh-TW": om
};
//#endregion
//#region node_modules/react-aria-components/dist/private/DragAndDrop.mjs
var cm = /*#__PURE__*/ (0, b.createContext)({}), lm = /*#__PURE__*/ (0, b.createContext)(null), um = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { render: n } = (0, b.useContext)(lm);
	return /*#__PURE__*/ b.createElement(b.Fragment, null, n(e, t));
});
function dm(e, t) {
	let n = e?.renderDropIndicator, r = e?.isVirtualDragging?.(), i = (0, b.useCallback)((e) => {
		if (r || t?.isDropTarget(e)) return n ? n(e) : /*#__PURE__*/ b.createElement(um, { target: e });
	}, [
		t?.target,
		r,
		n
	]);
	return e?.useDropIndicator ? i : void 0;
}
function fm(e, t, n) {
	let r = e.focusedKey, i = null;
	if (t?.isVirtualDragging?.() && n?.target?.type === "item" && (i = n.target.key, n.target.dropPosition === "after")) {
		let e = n.collection.getKeyAfter(i), t = null;
		if (e != null) {
			let r = n.collection.getItem(i)?.level ?? 0;
			for (; e != null;) {
				let i = n.collection.getItem(e);
				if (!i) break;
				if (i.type !== "item") {
					e = n.collection.getKeyAfter(e);
					continue;
				}
				if ((i.level ?? 0) <= r) break;
				t = e, e = n.collection.getKeyAfter(e);
			}
		}
		i = e ?? t ?? i;
	}
	return (0, b.useMemo)(() => new Set([r, i].filter((e) => e != null)), [r, i]);
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Header.mjs
var pm = /*#__PURE__*/ (0, b.createContext)({}), mm = /*#__PURE__*/ (0, b.createContext)(null);
function hm(e) {
	let t = (0, b.useRef)({});
	return /*#__PURE__*/ b.createElement(mm.Provider, { value: t }, e.children);
}
//#endregion
//#region node_modules/react-aria-components/dist/private/SelectionIndicator.mjs
var gm = /*#__PURE__*/ (0, b.createContext)({ isSelected: !1 }), _m = /*#__PURE__*/ (0, b.createContext)({});
(class extends ot {
	static {
		this.type = "separator";
	}
	filter(e, t) {
		let n = t.getItem(this.prevKey);
		if (n && n.type !== "separator") {
			let n = this.clone();
			return t.addDescendants(n, e), n;
		}
		return null;
	}
});
//#endregion
//#region node_modules/react-aria/dist/private/utils/inertValue.mjs
function vm(e) {
	let t = b.version.split(".");
	return parseInt(t[0], 10) >= 19 ? e : e ? "true" : void 0;
}
//#endregion
//#region node_modules/react-stately/dist/private/list/ListCollection.mjs
var ym = class {
	constructor(e) {
		this.keyMap = /* @__PURE__ */ new Map(), this.firstKey = null, this.lastKey = null, this.iterable = e;
		let t = (e) => {
			if (this.keyMap.set(e.key, e), e.childNodes && e.type === "section") for (let n of e.childNodes) t(n);
		};
		for (let n of e) t(n);
		let n = null, r = 0, i = 0;
		for (let [e, t] of this.keyMap) n ? (n.nextKey = e, t.prevKey = n.key) : (this.firstKey = e, t.prevKey = void 0), t.type === "item" && (t.index = r++), (t.type === "section" || t.type === "item") && i++, n = t, n.nextKey = void 0;
		this._size = i, this.lastKey = n?.key ?? null;
	}
	*[Symbol.iterator]() {
		yield* this.iterable;
	}
	get size() {
		return this._size;
	}
	getKeys() {
		return this.keyMap.keys();
	}
	getKeyBefore(e) {
		let t = this.keyMap.get(e);
		return t ? t.prevKey ?? null : null;
	}
	getKeyAfter(e) {
		let t = this.keyMap.get(e);
		return t ? t.nextKey ?? null : null;
	}
	getFirstKey() {
		return this.firstKey;
	}
	getLastKey() {
		return this.lastKey;
	}
	getItem(e) {
		return this.keyMap.get(e) ?? null;
	}
	at(e) {
		let t = [...this.getKeys()];
		return this.getItem(t[e]);
	}
	getChildren(e) {
		return this.keyMap.get(e)?.childNodes || [];
	}
}, bm = class e extends Set {
	constructor(t, n, r) {
		super(t), t instanceof e ? (this.anchorKey = n ?? t.anchorKey, this.currentKey = r ?? t.currentKey) : (this.anchorKey = n ?? null, this.currentKey = r ?? null);
	}
};
//#endregion
//#region node_modules/react-stately/dist/private/selection/useMultipleSelectionState.mjs
function xm(e, t) {
	if (e.size !== t.size) return !1;
	for (let n of e) if (!t.has(n)) return !1;
	return !0;
}
function Sm(e) {
	let { selectionMode: t = "none", disallowEmptySelection: n = !1, allowDuplicateSelectionEvents: r, selectionBehavior: i = "toggle", disabledBehavior: a = "all" } = e, o = (0, b.useRef)(!1), [, s] = (0, b.useState)(!1), c = (0, b.useRef)(null), l = (0, b.useRef)(null), [, u] = (0, b.useState)(null), [d, f] = No((0, b.useMemo)(() => Cm(e.selectedKeys), [e.selectedKeys]), (0, b.useMemo)(() => Cm(e.defaultSelectedKeys, new bm()), [e.defaultSelectedKeys]), e.onSelectionChange), p = (0, b.useMemo)(() => e.disabledKeys ? new Set(e.disabledKeys) : /* @__PURE__ */ new Set(), [e.disabledKeys]), [m, h] = (0, b.useState)(i);
	i === "replace" && m === "toggle" && typeof d == "object" && d.size === 0 && h("replace");
	let g = (0, b.useRef)(i);
	return (0, b.useEffect)(() => {
		i !== g.current && (h(i), g.current = i);
	}, [i]), {
		selectionMode: t,
		disallowEmptySelection: n,
		selectionBehavior: m,
		setSelectionBehavior: h,
		get isFocused() {
			return o.current;
		},
		setFocused(e) {
			o.current = e, s(e);
		},
		get focusedKey() {
			return c.current;
		},
		get childFocusStrategy() {
			return l.current;
		},
		setFocusedKey(e, t = "first") {
			c.current = e, l.current = t, u(e);
		},
		selectedKeys: d,
		setSelectedKeys(e) {
			(r || !xm(e, d)) && f(e);
		},
		disabledKeys: p,
		disabledBehavior: a
	};
}
function Cm(e, t) {
	return e ? e === "all" ? "all" : new bm(e) : t;
}
//#endregion
//#region node_modules/react-stately/dist/private/selection/SelectionManager.mjs
var wm = class e {
	constructor(e, t, n) {
		this.collection = e, this.state = t, this.allowsCellSelection = n?.allowsCellSelection ?? !1, this._isSelectAll = null, this.layoutDelegate = n?.layoutDelegate || null, this.fullCollection = n?.fullCollection || null;
	}
	get selectionMode() {
		return this.state.selectionMode;
	}
	get disallowEmptySelection() {
		return this.state.disallowEmptySelection;
	}
	get selectionBehavior() {
		return this.state.selectionBehavior;
	}
	setSelectionBehavior(e) {
		this.state.setSelectionBehavior(e);
	}
	get isFocused() {
		return this.state.isFocused;
	}
	setFocused(e) {
		this.state.setFocused(e);
	}
	get focusedKey() {
		return this.state.focusedKey;
	}
	get childFocusStrategy() {
		return this.state.childFocusStrategy;
	}
	setFocusedKey(e, t) {
		(e == null || this.collection.getItem(e)) && this.state.setFocusedKey(e, t);
	}
	get selectedKeys() {
		return this.state.selectedKeys === "all" ? new Set(this.getSelectAllKeys()) : this.state.selectedKeys;
	}
	get rawSelection() {
		return this.state.selectedKeys;
	}
	isSelected(e) {
		if (this.state.selectionMode === "none") return !1;
		let t = this.getKey(e);
		return t == null ? !1 : this.state.selectedKeys === "all" ? this.canSelectItem(t) : this.state.selectedKeys.has(t);
	}
	get isEmpty() {
		return this.state.selectedKeys !== "all" && this.state.selectedKeys.size === 0;
	}
	get isSelectAll() {
		if (this.isEmpty) return !1;
		if (this.state.selectedKeys === "all") return !0;
		if (this._isSelectAll != null) return this._isSelectAll;
		let e = this.getSelectAllKeys(), t = this.state.selectedKeys;
		return this._isSelectAll = e.every((e) => t.has(e)), this._isSelectAll;
	}
	get firstSelectedKey() {
		let e = null;
		for (let t of this.state.selectedKeys) {
			let n = this.collection.getItem(t);
			(!e || n && $s(this.collection, n, e) < 0) && (e = n);
		}
		return e?.key ?? null;
	}
	get lastSelectedKey() {
		let e = null;
		for (let t of this.state.selectedKeys) {
			let n = this.collection.getItem(t);
			(!e || n && $s(this.collection, n, e) > 0) && (e = n);
		}
		return e?.key ?? null;
	}
	get disabledKeys() {
		return this.state.disabledKeys;
	}
	get disabledBehavior() {
		return this.state.disabledBehavior;
	}
	extendSelection(e) {
		if (this.selectionMode === "none") return;
		if (this.selectionMode === "single") {
			this.replaceSelection(e);
			return;
		}
		let t = this.getKey(e);
		if (t == null) return;
		let n;
		if (this.state.selectedKeys === "all") n = new bm([t], t, t);
		else {
			let e = this.state.selectedKeys, r = e.anchorKey ?? t;
			n = new bm(e, r, t);
			for (let i of this.getKeyRange(r, e.currentKey ?? t)) n.delete(i);
			for (let e of this.getKeyRange(t, r)) this.canSelectItem(e) && n.add(e);
		}
		this.state.setSelectedKeys(n);
	}
	getKeyRange(e, t) {
		let n = this.collection.getItem(e), r = this.collection.getItem(t);
		return n && r ? $s(this.collection, n, r) <= 0 ? this.getKeyRangeInternal(e, t) : this.getKeyRangeInternal(t, e) : [];
	}
	getKeyRangeInternal(e, t) {
		if (this.layoutDelegate?.getKeyRange) return this.layoutDelegate.getKeyRange(e, t);
		let n = [], r = e;
		for (; r != null;) {
			let e = this.collection.getItem(r);
			if (e && (e.type === "item" || e.type === "cell" && this.allowsCellSelection) && n.push(r), r === t) return n;
			r = this.collection.getKeyAfter(r);
		}
		return [];
	}
	getKey(e) {
		let t = this.collection.getItem(e);
		if (!t || t.type === "cell" && this.allowsCellSelection) return e;
		for (; t && t.type !== "item" && t.parentKey != null;) t = this.collection.getItem(t.parentKey);
		return !t || t.type !== "item" ? null : t.key;
	}
	toggleSelection(e) {
		if (this.selectionMode === "none") return;
		if (this.selectionMode === "single" && !this.isSelected(e)) {
			this.replaceSelection(e);
			return;
		}
		let t = this.getKey(e);
		if (t == null) return;
		let n = new bm(this.state.selectedKeys === "all" ? this.getSelectAllKeys() : this.state.selectedKeys);
		n.has(t) ? n.delete(t) : this.canSelectItem(t) && (n.add(t), n.anchorKey = t, n.currentKey = t), !(this.disallowEmptySelection && n.size === 0) && this.state.setSelectedKeys(n);
	}
	replaceSelection(e) {
		if (this.selectionMode === "none") return;
		let t = this.getKey(e);
		if (t == null) return;
		let n = this.canSelectItem(t) ? new bm([t], t, t) : new bm();
		this.state.setSelectedKeys(n);
	}
	setSelectedKeys(e) {
		if (this.selectionMode === "none") return;
		let t = new bm();
		for (let n of e) {
			let e = this.getKey(n);
			if (e != null && (t.add(e), this.selectionMode === "single")) break;
		}
		this.state.setSelectedKeys(t);
	}
	getSelectAllKeys() {
		let e = this.fullCollection ?? this.collection, t = [], n = (r) => {
			for (; r != null;) {
				if (this.canSelectItemIn(r, e)) {
					let i = e.getItem(r);
					i?.type === "item" && t.push(r), i?.hasChildNodes && (this.allowsCellSelection || i.type !== "item") && n(Zs(Xs(i, e))?.key ?? null);
				}
				r = e.getKeyAfter(r);
			}
		};
		return n(e.getFirstKey()), t;
	}
	selectAll() {
		!this.isSelectAll && this.selectionMode === "multiple" && this.state.setSelectedKeys("all");
	}
	clearSelection() {
		!this.disallowEmptySelection && (this.state.selectedKeys === "all" || this.state.selectedKeys.size > 0) && this.state.setSelectedKeys(new bm());
	}
	toggleSelectAll() {
		this.isSelectAll ? this.clearSelection() : this.selectAll();
	}
	select(e, t) {
		this.selectionMode !== "none" && (this.selectionMode === "single" ? this.isSelected(e) && !this.disallowEmptySelection ? this.toggleSelection(e) : this.replaceSelection(e) : this.selectionBehavior === "toggle" || t && (t.pointerType === "touch" || t.pointerType === "virtual") ? this.toggleSelection(e) : this.replaceSelection(e));
	}
	isSelectionEqual(e) {
		if (e === this.state.selectedKeys) return !0;
		let t = this.selectedKeys;
		if (e.size !== t.size) return !1;
		for (let n of e) if (!t.has(n)) return !1;
		for (let n of t) if (!e.has(n)) return !1;
		return !0;
	}
	canSelectItem(e) {
		return this.canSelectItemIn(e, this.collection);
	}
	canSelectItemIn(e, t) {
		if (this.state.selectionMode === "none" || this.state.disabledKeys.has(e)) return !1;
		let n = t.getItem(e);
		return !(!n || n?.props?.isDisabled || n.type === "cell" && !this.allowsCellSelection);
	}
	isDisabled(e) {
		let t = this.collection.getItem(e);
		return this.state.disabledBehavior === "all" && (this.state.disabledKeys.has(e) || !!t?.props?.isDisabled) && t?.props?.disabledBehavior !== "selection";
	}
	isLink(e) {
		return !!this.collection.getItem(e)?.props?.href;
	}
	getItemProps(e) {
		return this.collection.getItem(e)?.props;
	}
	withCollection(t) {
		return new e(t, this.state, {
			allowsCellSelection: this.allowsCellSelection,
			layoutDelegate: this.layoutDelegate || void 0,
			fullCollection: this.fullCollection ?? this.collection
		});
	}
}, Tm = class {
	build(e, t) {
		return this.context = t, Em(() => this.iterateCollection(e));
	}
	*iterateCollection(e) {
		let { children: t, items: n } = e;
		if (b.isValidElement(t) && t.type === b.Fragment) yield* this.iterateCollection({
			children: t.props.children,
			items: n
		});
		else if (typeof t == "function") {
			if (!n) throw Error("props.children was a function but props.items is missing");
			let e = 0;
			for (let r of n) yield* this.getFullNode({
				value: r,
				index: e
			}, { renderer: t }), e++;
		} else {
			let e = [];
			b.Children.forEach(t, (t) => {
				t && e.push(t);
			});
			let n = 0;
			for (let t of e) {
				let e = this.getFullNode({
					element: t,
					index: n
				}, {});
				for (let t of e) n++, yield t;
			}
		}
	}
	getKey(e, t, n, r) {
		if (e.key != null) return e.key;
		if (t.type === "cell" && t.key != null) return `${r}${t.key}`;
		let i = t.value;
		if (i != null) {
			let e = i.key ?? i.id;
			if (e == null) throw Error("No key found for item");
			return e;
		}
		return r ? `${r}.${t.index}` : `$.${t.index}`;
	}
	getChildState(e, t) {
		return { renderer: t.renderer || e.renderer };
	}
	*getFullNode(e, t, n, r) {
		if (b.isValidElement(e.element) && e.element.type === b.Fragment) {
			let i = [];
			b.Children.forEach(e.element.props.children, (e) => {
				i.push(e);
			});
			let a = e.index ?? 0;
			for (let e of i) yield* this.getFullNode({
				element: e,
				index: a++
			}, t, n, r);
			return;
		}
		let i = e.element;
		if (!i && e.value && t && t.renderer) {
			let n = this.cache.get(e.value);
			if (n && (!n.shouldInvalidate || !n.shouldInvalidate(this.context))) {
				n.index = e.index, n.parentKey = r ? r.key : null, yield n;
				return;
			}
			i = t.renderer(e.value);
		}
		if (b.isValidElement(i)) {
			let a = i.type;
			if (typeof a != "function" && typeof a.getCollectionNode != "function") {
				let e = i.type;
				throw Error(`Unknown element <${e}> in collection.`);
			}
			let o = a.getCollectionNode(i.props, this.context), s = e.index ?? 0, c = o.next();
			for (; !c.done && c.value;) {
				let a = c.value;
				e.index = s;
				let l = a.key ?? null;
				l ??= a.element ? null : this.getKey(i, e, t, n);
				let u = [...this.getFullNode({
					...a,
					key: l,
					index: s,
					wrapper: Dm(e.wrapper, a.wrapper)
				}, this.getChildState(t, a), n ? `${n}${i.key}` : i.key, r)];
				for (let t of u) {
					if (t.value = a.value ?? e.value ?? null, t.value && this.cache.set(t.value, t), e.type && t.type !== e.type) throw Error(`Unsupported type <${Om(t.type)}> in <${Om(r?.type ?? "unknown parent type")}>. Only <${Om(e.type)}> is supported.`);
					s++, yield t;
				}
				c = o.next(u);
			}
			return;
		}
		if (e.key == null || e.type == null) return;
		let a = this, o = {
			type: e.type,
			props: e.props,
			key: e.key,
			parentKey: r ? r.key : null,
			value: e.value ?? null,
			level: (r?.level ?? 0) + +(r?.type === "item"),
			index: e.index,
			rendered: e.rendered,
			textValue: e.textValue ?? "",
			"aria-label": e["aria-label"],
			wrapper: e.wrapper,
			shouldInvalidate: e.shouldInvalidate,
			hasChildNodes: e.hasChildNodes || !1,
			childNodes: Em(function* () {
				if (!e.hasChildNodes || !e.childNodes) return;
				let n = 0;
				for (let r of e.childNodes()) {
					r.key != null && (r.key = `${o.key}${r.key}`);
					let e = a.getFullNode({
						...r,
						index: n
					}, a.getChildState(t, r), o.key, o);
					for (let t of e) n++, yield t;
				}
			})
		};
		yield o;
	}
	constructor() {
		this.cache = /* @__PURE__ */ new WeakMap();
	}
};
function Em(e) {
	let t = [], n = null;
	return { *[Symbol.iterator]() {
		for (let e of t) yield e;
		n ||= e();
		for (let e of n) t.push(e), yield e;
	} };
}
function Dm(e, t) {
	if (e && t) return (n) => e(t(n));
	if (e) return e;
	if (t) return t;
}
function Om(e) {
	return e[0].toUpperCase() + e.slice(1);
}
//#endregion
//#region node_modules/react-stately/dist/private/collections/useCollection.mjs
function km(e, t, n) {
	let r = (0, b.useMemo)(() => new Tm(), []), { children: i, items: a, collection: o } = e;
	return (0, b.useMemo)(() => o || t(r.build({
		children: i,
		items: a
	}, n)), [
		r,
		i,
		a,
		o,
		n,
		t
	]);
}
//#endregion
//#region node_modules/react-stately/dist/private/list/useListState.mjs
function Am(e) {
	let { filter: t, layoutDelegate: n } = e, r = Sm(e), i = (0, b.useMemo)(() => e.disabledKeys ? new Set(e.disabledKeys) : /* @__PURE__ */ new Set(), [e.disabledKeys]), a = km(e, (0, b.useCallback)((e) => t ? new ym(t(e)) : new ym(e), [t]), (0, b.useMemo)(() => ({ suppressTextValueWarning: e.suppressTextValueWarning }), [e.suppressTextValueWarning])), o = (0, b.useMemo)(() => new wm(a, r, { layoutDelegate: n }), [
		a,
		r,
		n
	]);
	return Mm(a, o), {
		collection: a,
		disabledKeys: i,
		selectionManager: o
	};
}
function jm(e, t) {
	let n = (0, b.useMemo)(() => t ? e.collection.filter(t) : e.collection, [e.collection, t]), r = e.selectionManager.withCollection(n);
	return Mm(n, r), {
		collection: n,
		selectionManager: r,
		disabledKeys: e.disabledKeys
	};
}
function Mm(e, t) {
	let n = (0, b.useRef)(null);
	(0, b.useEffect)(() => {
		if (t.focusedKey != null && !e.getItem(t.focusedKey) && n.current) {
			let r = n.current.getKeyAfter(t.focusedKey), i = null;
			for (; r != null;) {
				let a = e.getItem(r);
				if (a && a.type === "item" && !t.isDisabled(r)) {
					i = r;
					break;
				}
				r = n.current.getKeyAfter(r);
			}
			if (i == null) for (r = n.current.getKeyBefore(t.focusedKey); r != null;) {
				let a = e.getItem(r);
				if (a && a.type === "item" && !t.isDisabled(r)) {
					i = r;
					break;
				}
				r = n.current.getKeyBefore(r);
			}
			t.setFocusedKey(i);
		}
		n.current = e;
	}, [e, t]);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useLoadMoreSentinel.mjs
function Nm(e, t) {
	let { collection: n, onLoadMore: r, scrollOffset: i = 1, direction: a = "end" } = e, o = (0, b.useRef)(null), s = hi((e) => {
		for (let t of e) t.isIntersecting && r && r();
	});
	H(() => {
		if (t.current) {
			let e = 100 * i, n = a === "start" ? `${e}% 0px 0px 0px` : `0px ${e}% ${e}% ${e}%`;
			o.current = new IntersectionObserver(s, {
				root: $a(t?.current),
				rootMargin: n
			}), o.current.observe(t.current);
		}
		return () => {
			o.current && o.current.disconnect();
		};
	}, [
		n,
		t,
		i,
		a
	]);
}
//#endregion
//#region node_modules/react-aria-components/dist/private/ListBox.mjs
var Pm = /*#__PURE__*/ (0, b.createContext)(null), Fm = /*#__PURE__*/ (0, b.createContext)(null), Im = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	[e, t] = Wf(e, t, Pm);
	let n = (0, b.useContext)(Fm);
	return n ? /*#__PURE__*/ b.createElement(Rm, {
		state: n,
		props: e,
		listBoxRef: t
	}) : /*#__PURE__*/ b.createElement(Kr, { content: /*#__PURE__*/ b.createElement(ri, e) }, (n) => /*#__PURE__*/ b.createElement(Lm, {
		props: e,
		listBoxRef: t,
		collection: n
	}));
});
function Lm({ props: e, listBoxRef: t, collection: n }) {
	e = {
		...e,
		collection: n,
		children: null,
		items: null
	};
	let { layoutDelegate: r } = (0, b.useContext)(np), i = Am({
		...e,
		layoutDelegate: r
	});
	return /*#__PURE__*/ b.createElement(Rm, {
		state: i,
		props: e,
		listBoxRef: t
	});
}
function Rm({ state: e, props: t, listBoxRef: n }) {
	[t, n] = Wf(t, n, Xf);
	let { dragAndDropHooks: r, layout: i = "stack", orientation: a = "vertical", filter: o } = t, s = jm(e, o), { collection: c, selectionManager: l } = s, u = !!r?.useDraggableCollectionState, d = !!r?.useDroppableCollectionState, { direction: f } = Oi(), { disabledBehavior: p, disabledKeys: m } = l, h = ic({
		usage: "search",
		sensitivity: "base"
	}), { isVirtualized: g, layoutDelegate: _, dropTargetDelegate: v, CollectionRoot: y } = (0, b.useContext)(np), x = (0, b.useMemo)(() => t.keyboardDelegate || new ts({
		collection: c,
		collator: h,
		ref: n,
		disabledKeys: m,
		disabledBehavior: p,
		layout: i,
		orientation: a,
		direction: f,
		layoutDelegate: _
	}), [
		c,
		h,
		n,
		p,
		m,
		a,
		f,
		t.keyboardDelegate,
		i,
		_
	]), { listBoxProps: S } = Dc({
		...t,
		shouldSelectOnPressUp: u || t.shouldSelectOnPressUp,
		keyboardDelegate: x,
		isVirtualized: g
	}, s, n);
	(0, b.useRef)(u), (0, b.useRef)(d), (0, b.useEffect)(() => {}, [u, d]);
	let C, w, T, E = !1, D = null, O = (0, b.useRef)(null);
	if (u && r) {
		C = r.useDraggableCollectionState({
			collection: c,
			selectionManager: l,
			preview: r.renderDragPreview ? O : void 0
		}), r.useDraggableCollection({}, C, n);
		let e = r.DragPreview;
		D = r.renderDragPreview ? /*#__PURE__*/ b.createElement(e, { ref: O }, r.renderDragPreview) : null;
	}
	if (d && r) {
		w = r.useDroppableCollectionState({
			collection: c,
			selectionManager: l
		});
		let e = r.dropTargetDelegate || v || new r.ListDropTargetDelegate(c, n, {
			orientation: a,
			layout: i,
			direction: f
		});
		T = r.useDroppableCollection({
			keyboardDelegate: x,
			dropTargetDelegate: e
		}, w, n), E = w.isDropTarget({ type: "root" });
	}
	let { focusProps: k, isFocused: A, isFocusVisible: j } = pc(), M = s.collection.size === 0, N = {
		isDropTarget: E,
		isEmpty: M,
		isFocused: A,
		isFocusVisible: j,
		layout: t.layout || "stack",
		orientation: a,
		state: s
	}, ee = Hf({
		...t,
		children: void 0,
		defaultClassName: "react-aria-ListBox",
		values: N
	}), te = null;
	M && t.renderEmptyState && (te = /*#__PURE__*/ b.createElement("div", {
		role: "option",
		style: { display: "contents" }
	}, t.renderEmptyState(N)));
	let P = Yi(t, { global: !0 });
	return /*#__PURE__*/ b.createElement(wa, null, /*#__PURE__*/ b.createElement(Yf.div, {
		...U(P, ee, S, k, T?.collectionProps),
		ref: n,
		slot: t.slot || void 0,
		onScroll: t.onScroll,
		"data-drop-target": E || void 0,
		"data-empty": M || void 0,
		"data-focused": A || void 0,
		"data-focus-visible": j || void 0,
		"data-layout": t.layout || "stack",
		"data-orientation": a
	}, /*#__PURE__*/ b.createElement(Vf, { values: [
		[Pm, t],
		[Fm, s],
		[cm, {
			dragAndDropHooks: r,
			dragState: C,
			dropState: w
		}],
		[_m, { elementType: "div" }],
		[lm, { render: Vm }],
		[Qf, {
			name: "ListBoxSection",
			render: zm
		}]
	] }, /*#__PURE__*/ b.createElement(hm, null, /*#__PURE__*/ b.createElement(y, {
		collection: c,
		scrollRef: n,
		persistedKeys: fm(l, r, w),
		renderDropIndicator: dm(r, w)
	}))), te, D));
}
function zm(e, t, n, r = "react-aria-ListBoxSection") {
	let i = (0, b.useContext)(Fm), { dragAndDropHooks: a, dropState: o } = (0, b.useContext)(cm), { CollectionBranch: s } = (0, b.useContext)(np), [c, l] = Gf(), { headingProps: u, groupProps: d } = Oc({
		heading: l,
		"aria-label": e["aria-label"] ?? void 0
	}), f = Hf({
		...e,
		id: void 0,
		children: void 0,
		defaultClassName: r,
		values: void 0
	}), p = Yi(e, { global: !0 });
	return delete p.id, /*#__PURE__*/ b.createElement(Yf.section, {
		...U(p, f, d),
		ref: t
	}, /*#__PURE__*/ b.createElement(pm.Provider, { value: {
		...u,
		ref: c
	} }, /*#__PURE__*/ b.createElement(s, {
		collection: i.collection,
		parent: n,
		renderDropIndicator: dm(a, o)
	})));
}
var Bm = /*#__PURE__*/ ei(lt, function(e, t, n) {
	let r = kr(t), i = (0, b.useContext)(Fm), { dragAndDropHooks: a, dragState: o, dropState: s } = (0, b.useContext)(cm), c = o && !(o.isDisabled || o.selectionManager.isDisabled(n.key)), { optionProps: l, labelProps: u, descriptionProps: d, ...f } = kc({
		key: n.key,
		"aria-label": e?.["aria-label"]
	}, i, r), { hoverProps: p, isHovered: m } = bc({
		isDisabled: !f.allowsSelection && !f.hasAction && !c,
		onHoverStart: n.props.onHoverStart,
		onHoverChange: n.props.onHoverChange,
		onHoverEnd: n.props.onHoverEnd
	}), { keyboardProps: h } = Or(e), { focusProps: g } = mr(e), _ = null;
	o && a && (_ = a.useDraggableItem({
		key: n.key,
		hasAction: f.hasAction
	}, o));
	let v = null;
	s && a && (v = a.useDroppableItem({ target: {
		type: "item",
		key: n.key,
		dropPosition: "on"
	} }, s, r));
	let y = o && o.isDragging(n.key), x = Hf({
		...e,
		id: void 0,
		children: e.children,
		defaultClassName: "react-aria-ListBoxItem",
		values: {
			...f,
			isHovered: m,
			selectionMode: i.selectionManager.selectionMode,
			selectionBehavior: i.selectionManager.selectionBehavior,
			allowsDragging: !!o,
			isDragging: y,
			isDropTarget: v?.isDropTarget
		}
	});
	(0, b.useEffect)(() => {
		n.textValue;
	}, [n.textValue]);
	let S = e.href ? Yf.a : Yf.div, C = Yi(e, { global: !0 });
	return delete C.id, delete C.onClick, e.href && l.tabIndex == null && (l.tabIndex = -1), /*#__PURE__*/ b.createElement(S, {
		...U(C, x, l, p, h, g, _?.dragProps, v?.dropProps),
		ref: r,
		"data-allows-dragging": !!o || void 0,
		"data-selected": f.isSelected || void 0,
		"data-disabled": f.isDisabled || void 0,
		"data-hovered": m || void 0,
		"data-focused": f.isFocused || void 0,
		"data-focus-visible": f.isFocusVisible || void 0,
		"data-pressed": f.isPressed || void 0,
		"data-dragging": y || void 0,
		"data-drop-target": v?.isDropTarget || void 0,
		"data-selection-mode": i.selectionManager.selectionMode === "none" ? void 0 : i.selectionManager.selectionMode
	}, /*#__PURE__*/ b.createElement(Vf, { values: [[fp, { slots: {
		[$]: u,
		label: u,
		description: d
	} }], [gm, { isSelected: f.isSelected }]] }, x.children));
});
function Vm(e, t) {
	t = kr(t);
	let { dragAndDropHooks: n, dropState: r } = (0, b.useContext)(cm), { dropIndicatorProps: i, isHidden: a, isDropTarget: o } = n.useDropIndicator(e, r, t);
	return a ? null : /*#__PURE__*/ b.createElement(Um, {
		...e,
		dropIndicatorProps: i,
		isDropTarget: o,
		ref: t
	});
}
function Hm(e, t) {
	let { dropIndicatorProps: n, isDropTarget: r, ...i } = e, a = Hf({
		...i,
		defaultClassName: "react-aria-DropIndicator",
		values: { isDropTarget: r }
	});
	return /*#__PURE__*/ b.createElement(b.Fragment, null, /*#__PURE__*/ b.createElement(Yf.div, {
		...n,
		...a,
		role: "option",
		ref: t,
		"data-drop-target": r || void 0
	}));
}
var Um = /*#__PURE__*/ (0, b.forwardRef)(Hm);
ei(ct, function(e, t, n) {
	let r = (0, b.useContext)(Fm), { isLoading: i, onLoadMore: a, scrollOffset: o, ...s } = e, c = (0, b.useRef)(null);
	Nm((0, b.useMemo)(() => ({
		onLoadMore: a,
		collection: r?.collection,
		sentinelRef: c,
		scrollOffset: o
	}), [
		a,
		o,
		r?.collection
	]), c);
	let l = Hf({
		...s,
		id: void 0,
		children: n.rendered,
		defaultClassName: "react-aria-ListBoxLoadingIndicator",
		values: void 0
	});
	return /*#__PURE__*/ b.createElement(b.Fragment, null, /*#__PURE__*/ b.createElement("div", {
		style: {
			position: "relative",
			width: 0,
			height: 0
		},
		inert: vm(!0)
	}, /*#__PURE__*/ b.createElement("div", {
		"data-testid": "loadMoreSentinel",
		ref: c,
		style: {
			position: "absolute",
			height: 1,
			width: 1
		}
	})), i && l.children && /*#__PURE__*/ b.createElement(b.Fragment, null, /*#__PURE__*/ b.createElement(Yf.div, {
		...U(Yi(e, { global: !0 }), { tabIndex: -1 }),
		...l,
		role: "option",
		ref: t
	}, l.children)));
});
//#endregion
//#region node_modules/react-aria-components/dist/private/OverlayArrow.mjs
var Wm = /*#__PURE__*/ (0, b.createContext)({ placement: "bottom" });
//#endregion
//#region node_modules/react-stately/dist/private/overlays/useOverlayTriggerState.mjs
function Gm(e) {
	let [t, n] = No(e.isOpen, e.defaultOpen || !1, e.onOpenChange), [r, i] = (0, b.useState)(null);
	return {
		isOpen: t,
		setOpen: n,
		open: (0, b.useCallback)(() => {
			n(!0);
		}, [n]),
		close: (0, b.useCallback)(() => {
			n(!1);
		}, [n]),
		toggle: (0, b.useCallback)(() => {
			n(!t);
		}, [n, t]),
		point: r,
		setPoint: i
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/animation.mjs
function Km(e, t = !0) {
	let [n, r] = (0, b.useState)(!0), i = n && t;
	return H(() => {
		if (i && e.current && "getAnimations" in e.current) for (let t of e.current.getAnimations()) t instanceof CSSTransition && t.cancel();
	}, [e, i]), Jm(e, i, (0, b.useCallback)(() => r(!1), [])), i;
}
function qm(e, t) {
	let [n, r] = (0, b.useState)(t ? "open" : "closed");
	switch (n) {
		case "open":
			t || r("exiting");
			break;
		case "closed":
		case "exiting": t && r("open");
	}
	let i = n === "exiting";
	return Jm(e, i, (0, b.useCallback)(() => {
		r((e) => e === "exiting" ? "closed" : e);
	}, [])), i;
}
function Jm(e, t, n) {
	H(() => {
		if (t && e.current) {
			if (!("getAnimations" in e.current)) {
				n();
				return;
			}
			let t = e.current.getAnimations();
			if (t.length === 0) {
				n();
				return;
			}
			let r = !1;
			return Promise.allSettled(t.map((e) => e.finished)).then(() => {
				r || (0, Hr.flushSync)(() => {
					n();
				});
			}), () => {
				r = !0;
			};
		}
	}, [
		e,
		t,
		n
	]);
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Popover.mjs
var Ym = /*#__PURE__*/ (0, b.createContext)(null), Xm = /*#__PURE__*/ (0, b.createContext)(null), Zm = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	[e, t] = Wf(e, t, Ym);
	let n = (0, b.useContext)(eh), r = Gm(e), i = e.isOpen != null || e.defaultOpen != null || !n ? r : n, a = qm(t, i.isOpen), o = e.isExiting || !e.shouldSkipAnimation && a || !1, s = Lr(), { direction: c } = Oi();
	if (s) {
		let t = e.children;
		return typeof t == "function" && (t = t({
			trigger: e.trigger || null,
			placement: "bottom",
			isEntering: !1,
			isExiting: !1,
			defaultChildren: null
		})), /*#__PURE__*/ b.createElement(b.Fragment, null, t);
	}
	return i && !i.isOpen && !o ? null : /*#__PURE__*/ b.createElement(Qm, {
		...e,
		triggerRef: e.triggerRef,
		state: i,
		popoverRef: t,
		isExiting: o,
		dir: c
	});
});
function Qm({ state: e, isExiting: t, UNSTABLE_portalContainer: n, clearContexts: r, ...i }) {
	let a = (0, b.useRef)(null), o = (0, b.useRef)(null), s = (0, b.useContext)(Xm), c = s && i.trigger === "SubmenuTrigger", { popoverProps: l, underlayProps: u, arrowProps: d, placement: f, triggerAnchorPoint: p } = Xl({
		...i,
		offset: i.offset ?? 8,
		arrowRef: a,
		groupRef: c ? s : o
	}, e), m = i.popoverRef, h = Km(m, !!f), g = i.isEntering || !i.shouldSkipAnimation && h || !1, _ = Hf({
		...i,
		defaultClassName: "react-aria-Popover",
		values: {
			trigger: i.trigger || null,
			placement: f,
			isEntering: g,
			isExiting: t
		}
	}), v = !i.isNonModal || i.trigger === "SubmenuTrigger" || i.trigger === "PreviewTrigger", [y, x] = (0, b.useState)(i.trigger === "PreviewTrigger");
	H(() => {
		m.current && x(v && !m.current.querySelector("[role=dialog]"));
	}, [m, v]), (0, b.useEffect)(() => {
		y && i.trigger !== "PreviewTrigger" && (i.trigger !== "SubmenuTrigger" || Wn() !== "pointer") && m.current && !Nt(m.current) && er(m.current);
	}, [
		y,
		m,
		i.trigger
	]);
	let S = (0, b.useMemo)(() => {
		let e = _.children;
		if (r) for (let t of r) e = /*#__PURE__*/ b.createElement(t.Provider, { value: null }, e);
		return e;
	}, [_.children, r]), [C, w] = (0, b.useState)(null), T = (0, b.useCallback)(() => {
		i.triggerRef.current && w(i.triggerRef.current.getBoundingClientRect().width + "px");
	}, [i.triggerRef]);
	H(T, [T]), jc({
		ref: _.style?.["--trigger-width"] ? void 0 : i.triggerRef,
		onResize: T
	});
	let E = {
		...l.style,
		"--trigger-anchor-point": p ? `${p.x}px ${p.y}px` : void 0,
		..._.style,
		"--trigger-width": _.style?.["--trigger-width"] || C
	}, D = /*#__PURE__*/ b.createElement(Yf.div, {
		...U(Yi(i, { global: !0 }), l),
		..._,
		id: y ? i.id : void 0,
		role: y ? "dialog" : void 0,
		tabIndex: y ? -1 : void 0,
		"aria-label": i["aria-label"],
		"aria-labelledby": i["aria-labelledby"],
		ref: m,
		slot: i.slot || void 0,
		style: E,
		dir: i.dir,
		"data-trigger": i.trigger,
		"data-placement": f,
		"data-entering": g || void 0,
		"data-exiting": t || void 0
	}, !i.isNonModal && /*#__PURE__*/ b.createElement(ml, { onDismiss: e.close }), /*#__PURE__*/ b.createElement(Wm.Provider, { value: {
		...d,
		placement: f,
		ref: a
	} }, S), /*#__PURE__*/ b.createElement(ml, { onDismiss: e.close }));
	return c ? /*#__PURE__*/ b.createElement(uc, {
		...i,
		shouldContainFocus: y && i.trigger !== "PreviewTrigger",
		isExiting: t,
		portalContainer: n ?? s?.current ?? void 0
	}, D) : /*#__PURE__*/ b.createElement(uc, {
		...i,
		shouldContainFocus: y && i.trigger !== "PreviewTrigger",
		isExiting: t,
		portalContainer: n
	}, !i.isNonModal && e.isOpen && /*#__PURE__*/ b.createElement("div", {
		"data-testid": "underlay",
		...u,
		style: {
			position: "fixed",
			inset: 0
		}
	}), /*#__PURE__*/ b.createElement("div", {
		ref: o,
		style: { display: "contents" }
	}, /*#__PURE__*/ b.createElement(Xm.Provider, { value: o }, D)));
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Dialog.mjs
var $m = /*#__PURE__*/ (0, b.createContext)(null), eh = /*#__PURE__*/ (0, b.createContext)(null), th = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let n = e["aria-labelledby"];
	[e, t] = Wf(e, t, $m);
	let { dialogProps: r, titleProps: i, contentProps: a } = fc({
		...e,
		"aria-labelledby": n
	}, t), o = (0, b.useContext)(eh);
	!r["aria-label"] && !r["aria-labelledby"] && e["aria-labelledby"] && (r["aria-labelledby"] = e["aria-labelledby"]);
	let s = Hf({
		defaultClassName: "react-aria-Dialog",
		className: e.className,
		style: e.style,
		children: e.children,
		values: { close: o?.close || (() => {}) }
	}), c = Yi(e, { global: !0 });
	return /*#__PURE__*/ b.createElement(Yf.section, {
		...U(c, s, r),
		render: e.render,
		ref: t,
		slot: e.slot || void 0
	}, /*#__PURE__*/ b.createElement(Vf, { values: [
		[up, { slots: {
			[$]: {},
			title: {
				...i,
				level: 2
			}
		} }],
		[fp, { slots: {
			[$]: {},
			description: a
		} }],
		[op, { slots: {
			[$]: {},
			close: { onPress: () => o?.close() }
		} }]
	] }, s.children));
}), nh = Math.round(Math.random() * 1e10), rh = 0;
function ih(e) {
	let t = (0, b.useMemo)(() => e.name || `radio-group-${nh}-${++rh}`, [e.name]), [n, r] = No(e.value, e.defaultValue ?? null, e.onChange), [i] = (0, b.useState)(n), [a, o] = (0, b.useState)(null), s = bo({
		...e,
		value: n
	}), c = (t) => {
		!e.isReadOnly && !e.isDisabled && (r(t), s.commitValidation());
	}, l = s.displayValidation.isInvalid;
	return {
		...s,
		name: t,
		selectedValue: n,
		defaultSelectedValue: e.value === void 0 ? e.defaultValue ?? null : i,
		setSelectedValue: c,
		lastFocusedValue: a,
		setLastFocusedValue: o,
		isDisabled: e.isDisabled || !1,
		isReadOnly: e.isReadOnly || !1,
		isRequired: e.isRequired || !1,
		validationState: e.validationState || (l ? "invalid" : null),
		isInvalid: l
	};
}
//#endregion
//#region node_modules/react-aria-components/dist/private/RadioGroup.mjs
var ah = /*#__PURE__*/ (0, b.createContext)(null), oh = /*#__PURE__*/ (0, b.createContext)(null), sh = /*#__PURE__*/ (0, b.createContext)(null), ch = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	[e, t] = Wf(e, t, ah);
	let { validationBehavior: n } = Uf(hp) || {}, r = e.validationBehavior ?? n ?? "native", i = ih({
		...e,
		validationBehavior: r
	}), [a, o] = Gf(!e["aria-label"] && !e["aria-labelledby"]), { radioGroupProps: s, labelProps: c, descriptionProps: l, errorMessageProps: u, ...d } = $l({
		...e,
		label: o,
		validationBehavior: r
	}, i), f = Hf({
		...e,
		values: {
			orientation: e.orientation || "vertical",
			isDisabled: i.isDisabled,
			isReadOnly: i.isReadOnly,
			isRequired: i.isRequired,
			isInvalid: i.isInvalid,
			state: i
		},
		defaultClassName: "react-aria-RadioGroup"
	}), p = Yi(e, { global: !0 });
	return /*#__PURE__*/ b.createElement(Yf.div, {
		...U(p, f, s),
		ref: t,
		slot: e.slot || void 0,
		"data-orientation": e.orientation || "vertical",
		"data-invalid": i.isInvalid || void 0,
		"data-disabled": i.isDisabled || void 0,
		"data-readonly": i.isReadOnly || void 0,
		"data-required": i.isRequired || void 0
	}, /*#__PURE__*/ b.createElement(Vf, { values: [
		[sh, i],
		[rp, {
			...c,
			ref: a,
			elementType: "span"
		}],
		[fp, { slots: {
			description: l,
			errorMessage: u
		} }],
		[mp, d]
	] }, /*#__PURE__*/ b.createElement(hm, null, f.children)));
}), lh = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { inputRef: n = null, ...r } = e;
	[e, t] = Wf(r, t, oh);
	let i = b.useContext(sh), a = kr((0, b.useMemo)(() => ur(n, e.inputRef === void 0 ? null : e.inputRef), [n, e.inputRef])), o = Ql({
		...Kf(e),
		children: typeof e.children == "function" || e.children
	}, i, a);
	return /*#__PURE__*/ b.createElement(uh.Provider, { value: {
		...o,
		inputRef: a,
		defaultClassName: "react-aria-Radio"
	} }, /*#__PURE__*/ b.createElement(dh, {
		...e,
		ref: t
	}));
}), uh = /*#__PURE__*/ (0, b.createContext)(null), dh = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { labelProps: n, inputProps: r, isSelected: i, isDisabled: a, isPressed: o, defaultClassName: s, inputRef: c } = (0, b.useContext)(uh), l = b.useContext(sh), { isFocused: u, isFocusVisible: d, focusProps: f } = pc(), p = a || l.isReadOnly, { hoverProps: m, isHovered: h } = bc({
		...e,
		isDisabled: p
	}), g = Hf({
		...e,
		defaultClassName: s,
		values: {
			isSelected: i,
			isPressed: o,
			isHovered: h,
			isFocused: u,
			isFocusVisible: d,
			isDisabled: a,
			isReadOnly: l.isReadOnly,
			isInvalid: l.isInvalid,
			isRequired: l.isRequired
		}
	}), _ = Yi(e, { global: !0 });
	return delete _.id, delete _.onClick, /*#__PURE__*/ b.createElement(Yf.label, {
		...U(_, n, m, g),
		ref: t,
		"data-selected": i || void 0,
		"data-pressed": o || void 0,
		"data-hovered": h || void 0,
		"data-focused": u || void 0,
		"data-focus-visible": d || void 0,
		"data-disabled": a || void 0,
		"data-readonly": l.isReadOnly || void 0,
		"data-invalid": l.isInvalid || void 0,
		"data-required": l.isRequired || void 0
	}, /*#__PURE__*/ b.createElement(Ro, { elementType: "span" }, /*#__PURE__*/ b.createElement("input", {
		...U(r, f),
		ref: c
	})), g.children);
});
//#endregion
//#region node_modules/react-stately/dist/private/select/useSelectState.mjs
function fh(e) {
	let { selectionMode: t = "single", shouldCloseOnSelect: n = t === "single" } = e, r = Gm(e), [i, a] = (0, b.useState)(null), o = (0, b.useMemo)(() => e.defaultValue === void 0 ? t === "single" ? e.defaultSelectedKey ?? null : [] : e.defaultValue, [
		e.defaultValue,
		e.defaultSelectedKey,
		t
	]), [s, c] = No((0, b.useMemo)(() => e.value === void 0 ? t === "single" ? e.selectedKey : void 0 : e.value, [
		e.value,
		e.selectedKey,
		t
	]), o, e.onChange), l = t === "single" && Array.isArray(s) ? s[0] : s, u = (n) => {
		if (t === "single") {
			let t = Array.isArray(n) ? n[0] ?? null : n;
			c(t), t !== l && e.onSelectionChange?.(t);
		} else {
			let e = [];
			Array.isArray(n) ? e = n : n != null && (e = [n]), c(e);
		}
	}, d = Am({
		...e,
		selectionMode: t,
		disallowEmptySelection: t === "single",
		allowDuplicateSelectionEvents: !0,
		selectedKeys: (0, b.useMemo)(() => ph(l), [l]),
		onSelectionChange: (e) => {
			if (e !== "all") {
				if (t === "single") {
					let t = e.values().next().value ?? null;
					u(t);
				} else u([...e]);
				n && r.close(), m.commitValidation();
			}
		}
	}), f = d.selectionManager.firstSelectedKey, p = (0, b.useMemo)(() => [...d.selectionManager.selectedKeys].map((e) => d.collection.getItem(e)).filter((e) => e != null), [d.selectionManager.selectedKeys, d.collection]), m = bo({
		...e,
		value: Array.isArray(l) && l.length === 0 ? null : l
	}), [h, g] = (0, b.useState)(!1), [_] = (0, b.useState)(l);
	return {
		...m,
		...d,
		...r,
		value: l,
		defaultValue: o ?? _,
		setValue: u,
		selectedKey: f,
		setSelectedKey: u,
		selectedItem: p[0] ?? null,
		selectedItems: p,
		defaultSelectedKey: e.defaultSelectedKey ?? (e.selectionMode === "single" ? _ : null),
		focusStrategy: i,
		open(t = null) {
			(d.collection.size !== 0 || e.allowsEmptyCollection) && (a(t), r.open());
		},
		toggle(t = null) {
			(d.collection.size !== 0 || e.allowsEmptyCollection) && (a(t), r.toggle());
		},
		isFocused: h,
		setFocused: g
	};
}
function ph(e) {
	if (e !== void 0) return e === null ? [] : Array.isArray(e) ? e : [e];
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Select.mjs
function mh(e) {
	return e && e.__esModule ? e.default : e;
}
var hh = /*#__PURE__*/ (0, b.createContext)(null), gh = /*#__PURE__*/ (0, b.createContext)(null), _h = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, hh);
	let { children: n, isDisabled: r = !1, isInvalid: i = !1, isRequired: a = !1 } = e, o = (0, b.useMemo)(() => typeof n == "function" ? n({
		isOpen: !1,
		isDisabled: r,
		isInvalid: i,
		isRequired: a,
		isFocused: !1,
		isFocusVisible: !1,
		defaultChildren: null
	}) : n, [
		n,
		r,
		i,
		a
	]);
	return /*#__PURE__*/ b.createElement(Kr, { content: o }, (n) => /*#__PURE__*/ b.createElement(yh, {
		props: e,
		collection: n,
		selectRef: t
	}));
}), vh = [
	rp,
	op,
	fp
];
function yh({ props: e, selectRef: t, collection: n }) {
	let { validationBehavior: r } = Uf(hp) || {}, i = e.validationBehavior ?? r ?? "native", a = fh({
		...e,
		collection: n,
		children: void 0,
		validationBehavior: i
	}), { isFocusVisible: o, focusProps: s } = pc({ within: !0 }), c = (0, b.useRef)(null), [l, u] = Gf(!e["aria-label"] && !e["aria-labelledby"]), { labelProps: d, triggerProps: f, valueProps: p, menuProps: m, descriptionProps: h, errorMessageProps: g, hiddenSelectProps: _, ...v } = tu({
		...Kf(e),
		label: u,
		validationBehavior: i
	}, a, c), y = (0, b.useMemo)(() => ({
		isOpen: a.isOpen,
		isFocused: a.isFocused,
		isFocusVisible: o,
		isDisabled: e.isDisabled || !1,
		isInvalid: v.isInvalid || !1,
		isRequired: e.isRequired || !1
	}), [
		a.isOpen,
		a.isFocused,
		o,
		e.isDisabled,
		v.isInvalid,
		e.isRequired
	]), x = Hf({
		...e,
		values: y,
		defaultClassName: "react-aria-Select"
	}), S = Yi(e, { global: !0 });
	delete S.id;
	let C = (0, b.useRef)(null);
	return /*#__PURE__*/ b.createElement(Vf, { values: [
		[hh, e],
		[gh, a],
		[bh, p],
		[rp, {
			...d,
			ref: l,
			elementType: "span"
		}],
		[op, {
			...f,
			ref: c,
			isPressed: a.isOpen,
			autoFocus: e.autoFocus
		}],
		[eh, a],
		[Ym, {
			trigger: "Select",
			triggerRef: c,
			scrollRef: C,
			placement: "bottom start",
			"aria-labelledby": m["aria-labelledby"],
			clearContexts: vh
		}],
		[Pm, {
			...m,
			ref: C
		}],
		[Fm, a],
		[fp, { slots: {
			description: h,
			errorMessage: g
		} }],
		[mp, v]
	] }, /*#__PURE__*/ b.createElement(Yf.div, {
		...U(S, x, s),
		ref: t,
		slot: e.slot || void 0,
		"data-focused": a.isFocused || void 0,
		"data-focus-visible": o || void 0,
		"data-open": a.isOpen || void 0,
		"data-disabled": e.isDisabled || void 0,
		"data-invalid": v.isInvalid || void 0,
		"data-required": e.isRequired || void 0
	}, x.children, /*#__PURE__*/ b.createElement(ru, {
		..._,
		autoComplete: e.autoComplete
	})));
}
var bh = /*#__PURE__*/ (0, b.createContext)(null), xh = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, bh);
	let n = (0, b.useContext)(gh), { placeholder: r } = Uf(hh), i = n.selectedItems.map((e) => {
		let t = e.props?.children;
		return typeof t == "function" && (t = t({
			isHovered: !1,
			isPressed: !1,
			isSelected: !1,
			isFocused: !1,
			isFocusVisible: !1,
			isDisabled: !1,
			selectionMode: "single",
			selectionBehavior: "toggle"
		})), t;
	}), a = mc(), o = (0, b.useMemo)(() => n.selectedItems.map((e) => e?.textValue), [n.selectedItems]), s = n.selectionManager.selectionMode, c = (0, b.useMemo)(() => s === "single" ? o[0] ?? "" : a.format(o), [
		s,
		a,
		o
	]), l = (0, b.useMemo)(() => {
		if (s === "single") return i[0];
		let e = a.formatToParts(o);
		if (e.length === 0) return null;
		let t = 0;
		return e.map((e) => e.type === "element" ? /*#__PURE__*/ b.createElement(b.Fragment, { key: t }, i[t++]) : e.value);
	}, [
		s,
		a,
		o,
		i
	]), u = Hi(mh(sm), "react-aria-components"), d = Hf({
		...e,
		defaultChildren: l ?? r ?? u.format("selectPlaceholder"),
		defaultClassName: "react-aria-SelectValue",
		values: {
			selectedItem: n.selectedItems[0]?.value ?? null,
			selectedItems: (0, b.useMemo)(() => n.selectedItems.map((e) => e.value ?? null), [n.selectedItems]),
			selectedText: c,
			isPlaceholder: n.selectedItems.length === 0,
			state: n
		}
	}), f = Yi(e, { global: !0 });
	return /*#__PURE__*/ b.createElement(Yf.span, {
		ref: t,
		...f,
		...d,
		"data-placeholder": n.selectedItems.length === 0 || void 0
	}, /*#__PURE__*/ b.createElement(fp.Provider, { value: void 0 }, d.children));
}), Sh = /*#__PURE__*/ (0, b.createContext)(null), Ch = /*#__PURE__*/ (0, b.createContext)(null), wh = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { inputRef: n = null, ...r } = e;
	[e, t] = Wf(r, t, Sh);
	let i = kr((0, b.useMemo)(() => ur(n, e.inputRef === void 0 ? null : e.inputRef), [n, e.inputRef])), a = Po(e), o = iu({
		...Kf(e),
		children: typeof e.children == "function" || e.children
	}, a, i);
	return /*#__PURE__*/ b.createElement(Vf, { values: [[Ch, a], [Th, {
		...o,
		inputRef: i,
		defaultClassName: "react-aria-Switch"
	}]] }, /*#__PURE__*/ b.createElement(Eh, {
		...e,
		ref: t
	}));
}), Th = /*#__PURE__*/ (0, b.createContext)(null), Eh = /*#__PURE__*/ (0, b.forwardRef)(function(e, t) {
	let { labelProps: n, inputProps: r, isSelected: i, isDisabled: a, isReadOnly: o, isPressed: s, isInvalid: c, inputRef: l, defaultClassName: u, isRequired: d } = (0, b.useContext)(Th), { isFocused: f, isFocusVisible: p, focusProps: m } = pc(), h = a || o, g = (0, b.useContext)(Ch), { hoverProps: _, isHovered: v } = bc({
		...e,
		isDisabled: h
	}), y = Hf({
		...e,
		defaultClassName: u,
		values: {
			isSelected: i,
			isPressed: s,
			isHovered: v,
			isFocused: f,
			isFocusVisible: p,
			isDisabled: a,
			isReadOnly: o,
			isInvalid: c,
			isRequired: d || !1,
			state: g
		}
	}), x = Yi(e, { global: !0 });
	return delete x.id, delete x.onClick, /*#__PURE__*/ b.createElement(Yf.label, {
		...U(x, n, _, y),
		ref: t,
		slot: e.slot || void 0,
		"data-selected": i || void 0,
		"data-pressed": s || void 0,
		"data-hovered": v || void 0,
		"data-focused": f || void 0,
		"data-focus-visible": p || void 0,
		"data-disabled": a || void 0,
		"data-readonly": o || void 0,
		"data-invalid": c || void 0,
		"data-required": d || void 0
	}, /*#__PURE__*/ b.createElement(Ro, { elementType: "span" }, /*#__PURE__*/ b.createElement("input", {
		...U(r, m),
		ref: l
	})), y.children);
}), Dh = /*#__PURE__*/ (0, b.createContext)({}), Oh = /*#__PURE__*/ (0, b.createContext)(null), kh = /*#__PURE__*/ Ir(function(e, t) {
	[e, t] = Wf(e, t, Oh);
	let { validationBehavior: n } = Uf(hp) || {}, r = e.validationBehavior ?? n ?? "native", i = (0, b.useRef)(null);
	[e, i] = Wf(e, i, Zf);
	let [a, o] = Gf(!e["aria-label"] && !e["aria-labelledby"]), [s, c] = (0, b.useState)("input"), { labelProps: l, inputProps: u, descriptionProps: d, errorMessageProps: f, ...p } = zo({
		...Kf(e),
		inputElementType: s,
		label: o,
		validationBehavior: r
	}, i), m = (0, b.useCallback)((e) => {
		i.current = e, e && c(e instanceof HTMLTextAreaElement ? "textarea" : "input");
	}, [i]), h = Hf({
		...e,
		values: {
			isDisabled: e.isDisabled || !1,
			isInvalid: p.isInvalid,
			isReadOnly: e.isReadOnly || !1,
			isRequired: e.isRequired || !1
		},
		defaultClassName: "react-aria-TextField"
	}), g = Yi(e, { global: !0 });
	return delete g.id, /*#__PURE__*/ b.createElement(Yf.div, {
		...g,
		...h,
		ref: t,
		slot: e.slot || void 0,
		"data-disabled": e.isDisabled || void 0,
		"data-invalid": p.isInvalid || void 0,
		"data-readonly": e.isReadOnly || void 0,
		"data-required": e.isRequired || void 0
	}, /*#__PURE__*/ b.createElement(Vf, { values: [
		[rp, {
			...l,
			ref: a
		}],
		[wp, {
			...u,
			ref: m
		}],
		[Dh, {
			...u,
			ref: m
		}],
		[Sp, {
			role: "presentation",
			isInvalid: p.isInvalid,
			isDisabled: e.isDisabled || !1
		}],
		[fp, { slots: {
			description: d,
			errorMessage: f
		} }],
		[mp, p]
	] }, h.children));
}), Ah = Kd({
	sm: {
		track: "h-4 w-7",
		trackRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[3px]"
		},
		onShadow: "shadow-[inset_0_1px_0_0_rgb(255_255_255/0.25),inset_0_0_0_0.5px_var(--color-accent-500)]",
		thumb: "size-3",
		thumbRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[1px]"
		},
		offset: "left-0.5 top-0.5",
		travel: "translate-x-3",
		chip: "size-[5px] border-[0.25px] shadow-[0_2px_2px_0_rgb(0_0_0/0.03)]",
		chipRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[0.5px]"
		}
	},
	md: {
		track: "h-6 w-[42px]",
		trackRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[4.5px]"
		},
		onShadow: "shadow-[inset_0_1.5px_0_0_rgb(255_255_255/0.25),inset_0_0_0_0.75px_var(--color-accent-500)]",
		thumb: "size-[18px]",
		thumbRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[1.5px]"
		},
		offset: "left-[3px] top-[3px]",
		travel: "translate-x-[18px]",
		chip: "size-[7.5px] border-[0.375px] shadow-[0_3px_3px_0_rgb(0_0_0/0.03)]",
		chipRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[0.75px]"
		}
	},
	lg: {
		track: "h-8 w-14",
		trackRadius: {
			pill: "rounded-full",
			rectangle: "rounded-md"
		},
		onShadow: "shadow-checkbox-selected",
		thumb: "size-6",
		thumbRadius: {
			pill: "rounded-full",
			rectangle: "rounded-xs"
		},
		offset: "left-1 top-1",
		travel: "translate-x-6",
		chip: "size-[10px] border-[0.5px] shadow-[0_4px_4px_0_rgb(0_0_0/0.03)]",
		chipRadius: {
			pill: "rounded-full",
			rectangle: "rounded-[1px]"
		}
	}
});
function jh({ state: e, size: t = "md", shape: n = "pill" }) {
	let r = Ah[t];
	return /* @__PURE__ */ (0, x.jsx)("span", {
		"aria-hidden": !0,
		className: Gd("relative shrink-0 transition-colors duration-200 ease", r.track, r.trackRadius[n], e.isSelected ? Gd("bg-linear-to-b from-accent-500 to-accent-600", r.onShadow) : "bg-background-tertiary-default", e.isDisabled && "opacity-50", e.isFocusVisible && "ring-2 ring-border-focus-ring ring-offset-2"),
		children: /* @__PURE__ */ (0, x.jsx)("span", {
			className: Gd("absolute flex items-center justify-center", "bg-linear-to-b from-control-indicator-background from-[43.837%] to-control-indicator-background-subtle", "shadow-[0_3px_3px_0_rgb(0_0_0/0.03),0_0.75px_0_0_rgb(0_0_0/0.05)]", "transition-transform duration-200 ease", r.thumb, r.thumbRadius[n], r.offset, e.isSelected && r.travel),
			children: /* @__PURE__ */ (0, x.jsx)("span", { className: Gd("border-solid bg-linear-to-t from-[43.837%]", r.chip, r.chipRadius[n], e.isSelected ? "border-accent-600 from-switch-on-chip-start to-switch-on-chip-end" : "border-border-button-default/50 from-switch-off-chip-start to-switch-off-chip-end") })
		})
	});
}
function Mh({ className: e, children: t, size: n = "md", shape: r = "pill", ref: i, ...a }) {
	return /* @__PURE__ */ (0, x.jsx)(wh, {
		ref: i,
		...a,
		className: (t) => Gd("group inline-flex items-center gap-2 select-none", t.isDisabled ? "cursor-not-allowed" : "cursor-pointer", typeof e == "function" ? e(t) : e),
		children: (e) => /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsx)(jh, {
			state: e,
			size: n,
			shape: r
		}), t != null && t !== !1 && /* @__PURE__ */ (0, x.jsx)("span", {
			className: "text-body-medium text-text-primary",
			children: t
		})] })
	});
}
//#endregion
//#region src/react/boardui/components/base/buttons/link-button.tsx
var Nh = Kd({
	base: [
		"inline-flex items-center justify-center gap-1 whitespace-nowrap",
		"font-sans select-none cursor-pointer rounded-sm",
		"underline-offset-3 hover:underline",
		"transition-colors duration-150 ease",
		"outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus-ring",
		"disabled:cursor-not-allowed disabled:no-underline aria-disabled:cursor-not-allowed aria-disabled:no-underline"
	].join(" "),
	size: {
		medium: "text-body-medium",
		small: "text-body-medium",
		xs: "text-caption-1-semibold"
	},
	icon: {
		medium: "size-5 shrink-0",
		small: "size-[18px] shrink-0",
		xs: "size-3.5 shrink-0"
	},
	variant: {
		primary: ["text-accent-600 active:text-accent-800", "disabled:text-text-tertiary aria-disabled:text-text-tertiary"].join(" "),
		secondary: ["text-text-secondary active:text-text-primary", "disabled:text-text-tertiary aria-disabled:text-text-tertiary"].join(" ")
	}
});
function Ph({ variant: e = "primary", size: t = "medium", leadingIcon: n, trailingIcon: r, children: i, className: a, disabled: o = !1, ...s }) {
	let c = Gd(Nh.base, Nh.size[t], Nh.variant[e], a), l = /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [
		n ? /* @__PURE__ */ (0, x.jsx)(n, {
			className: Nh.icon[t],
			"aria-hidden": !0
		}) : null,
		i != null && /* @__PURE__ */ (0, x.jsx)("span", { children: i }),
		r ? /* @__PURE__ */ (0, x.jsx)(r, {
			className: Nh.icon[t],
			"aria-hidden": !0
		}) : null
	] });
	if (s.href !== void 0) {
		let { ref: e, href: t, ...n } = s;
		return /* @__PURE__ */ (0, x.jsx)("a", {
			ref: e,
			href: o ? void 0 : t,
			"aria-disabled": o || void 0,
			className: c,
			...n,
			children: l
		});
	}
	let { ref: u, type: d = "button", ...f } = s;
	return /* @__PURE__ */ (0, x.jsx)("button", {
		ref: u,
		type: d,
		disabled: o,
		className: c,
		...f,
		children: l
	});
}
//#endregion
//#region src/react/settings/section.tsx
function Fh({ title: e, id: t, onSubmit: n, children: r }) {
	let i = /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsx)(zf, { children: e }), /* @__PURE__ */ (0, x.jsx)(Rf, { children: r })] });
	return n ? /* @__PURE__ */ (0, x.jsx)("form", {
		id: t,
		"aria-label": e,
		noValidate: !0,
		onSubmit: n,
		className: "flex w-full flex-col gap-2",
		children: i
	}) : /* @__PURE__ */ (0, x.jsx)("section", {
		id: t,
		"aria-label": e,
		className: "flex w-full flex-col gap-2",
		children: i
	});
}
function Ih({ children: e }) {
	return /* @__PURE__ */ (0, x.jsx)("div", {
		className: "flex flex-col",
		children: e
	});
}
function Lh({ divided: e = !1, children: t }) {
	return e ? /* @__PURE__ */ (0, x.jsx)("div", {
		className: "flex flex-col gap-4 border-t border-separator-border py-4 pr-3",
		children: t
	}) : /* @__PURE__ */ (0, x.jsx)("div", {
		className: "flex flex-col gap-4 py-4 pr-3",
		children: t
	});
}
function Rh({ status: e, children: t }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "flex flex-wrap items-center justify-end gap-3 border-t border-separator-border py-3 pr-3",
		children: [e ? /* @__PURE__ */ (0, x.jsx)("div", {
			className: "mr-auto min-w-0 text-body-2-regular text-text-secondary",
			children: e
		}) : null, t]
	});
}
function zh({ role: e, children: t }) {
	return /* @__PURE__ */ (0, x.jsx)("p", {
		role: e,
		className: "text-body-2-regular text-text-secondary",
		children: t
	});
}
function Bh({ children: e }) {
	return /* @__PURE__ */ (0, x.jsx)("p", {
		role: "alert",
		className: "text-body-2-regular text-text-error-primary",
		children: e
	});
}
function Vh({ children: e }) {
	return /* @__PURE__ */ (0, x.jsx)("p", {
		className: "text-body-medium text-text-primary",
		children: e
	});
}
function Hh({ href: e, children: t }) {
	return /* @__PURE__ */ (0, x.jsx)(Ph, {
		href: e,
		target: "_blank",
		rel: "noreferrer",
		size: "small",
		trailingIcon: du,
		children: t
	});
}
function Uh({ children: e }) {
	return /* @__PURE__ */ (0, x.jsx)("dl", {
		className: "flex flex-col",
		children: e
	});
}
function Wh({ term: e, children: t }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "flex min-h-11 items-center justify-between gap-4 border-b border-separator-border py-2.5 pr-3 last:border-b-0",
		children: [/* @__PURE__ */ (0, x.jsx)("dt", {
			className: "flex shrink-0 items-center gap-2 text-body-regular text-text-secondary",
			children: e
		}), /* @__PURE__ */ (0, x.jsx)("dd", {
			className: "flex min-w-0 flex-wrap items-center justify-end gap-2 text-right text-body-regular break-all text-text-primary",
			children: t
		})]
	});
}
function Gh({ summary: e, children: t }) {
	let n = (0, b.useId)(), r = (0, b.useRef)(null), i = (0, b.useRef)(null), [a, s] = (0, b.useState)(!1);
	return /* @__PURE__ */ (0, x.jsxs)("details", {
		ref: r,
		children: [/* @__PURE__ */ (0, x.jsxs)("summary", {
			"aria-expanded": a,
			"aria-controls": n,
			onClick: (e) => {
				e.preventDefault(), !(!r.current || !i.current) && (o(r.current, i.current, !a), s(!a));
			},
			className: "flex w-fit cursor-pointer list-none items-center gap-1 rounded-sm text-body-2-medium text-text-secondary outline-none select-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring",
			children: [/* @__PURE__ */ (0, x.jsx)(lu, {
				"aria-hidden": !0,
				className: a ? "size-4 shrink-0 rotate-90 transition-transform" : "size-4 shrink-0 transition-transform"
			}), e]
		}), /* @__PURE__ */ (0, x.jsx)("div", {
			ref: i,
			id: n,
			inert: !a,
			children: /* @__PURE__ */ (0, x.jsx)("div", {
				className: "flex flex-col gap-2 pt-3",
				children: t
			})
		})]
	});
}
function Kh({ name: e }) {
	return /* @__PURE__ */ (0, x.jsx)("svg", {
		"aria-hidden": !0,
		viewBox: "0 0 24 24",
		fill: "none",
		className: "size-4 shrink-0 stroke-current stroke-2",
		children: /* @__PURE__ */ (0, x.jsx)("use", { href: `#i-${e}` })
	});
}
function qh({ mark: e }) {
	return e.startsWith("data:image/png;base64,") ? /* @__PURE__ */ (0, x.jsx)("img", {
		src: e,
		alt: "",
		width: 16,
		height: 16,
		className: "size-4 shrink-0"
	}) : /* @__PURE__ */ (0, x.jsx)(Kh, { name: e });
}
//#endregion
//#region src/react/settings/use-action.ts
function Jh(e = "") {
	let t = (0, b.useRef)(null), [n, r] = (0, b.useState)(""), [i, a] = (0, b.useState)(e);
	(0, b.useEffect)(() => () => t.current?.abort(), []);
	async function o(e, n, i, o) {
		if (t.current) return;
		let s = new AbortController();
		t.current = s, r(e), a("");
		try {
			let e = await n(s.signal);
			s.signal.aborted || i(e);
		} catch (e) {
			if (s.signal.aborted) return;
			o ? o(e) : a(Zd(e));
		} finally {
			t.current === s && (t.current = null), s.signal.aborted || r("");
		}
	}
	return {
		run: o,
		busy: n,
		error: i,
		setError: a
	};
}
function Yh(e) {
	return e ? {
		"aria-busy": !0,
		"aria-disabled": !0
	} : {};
}
//#endregion
//#region src/react/settings/general-settings.tsx
function Xh({ data: e, receipt: t }) {
	return e.startup ? /* @__PURE__ */ (0, x.jsx)(Zh, {
		startup: e.startup,
		receipt: t
	}) : null;
}
function Zh({ startup: e, receipt: t }) {
	let [n, r] = (0, b.useState)(e.enabled), [i, a] = (0, b.useState)(e.silent), [o, s] = (0, b.useState)(e.desktop), c = Jh(), l = e.available && !e.desktop_message;
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "开机自启",
		onSubmit: (r) => {
			r.preventDefault(), e.available && c.run("save", (e) => $d("/api/configuration/startup", {
				enabled: n,
				silent: i,
				desktop: o
			}, "POST", e), () => t("已保存配置"));
		},
		children: [
			/* @__PURE__ */ (0, x.jsxs)(Ih, { children: [
				/* @__PURE__ */ (0, x.jsx)(Bf, {
					label: "开机后启动 Peach",
					children: /* @__PURE__ */ (0, x.jsx)(Mh, {
						"aria-label": "开机后启动 Peach",
						isSelected: n,
						isDisabled: !e.available,
						onChange: r
					})
				}),
				/* @__PURE__ */ (0, x.jsx)(Bf, {
					label: "静默启动",
					description: "静默启动仅显示托盘，开机后启动 Peach 打开时生效。",
					children: /* @__PURE__ */ (0, x.jsx)(Mh, {
						"aria-label": "静默启动",
						isSelected: i,
						isDisabled: !e.available || !n,
						onChange: a
					})
				}),
				/* @__PURE__ */ (0, x.jsx)(Bf, {
					label: "在桌面创建快捷方式",
					description: e.desktop_message || "双击图标打开 Peach 网页；卸载时一并移除。",
					children: /* @__PURE__ */ (0, x.jsx)(Mh, {
						"aria-label": "在桌面创建快捷方式",
						isSelected: o,
						isDisabled: !l,
						onChange: s
					})
				})
			] }),
			e.message || c.error ? /* @__PURE__ */ (0, x.jsxs)(Lh, {
				divided: !0,
				children: [e.message ? /* @__PURE__ */ (0, x.jsx)(zh, { children: e.message }) : null, c.error ? /* @__PURE__ */ (0, x.jsx)(Bh, { children: c.error }) : null]
			}) : null,
			/* @__PURE__ */ (0, x.jsx)(Rh, { children: /* @__PURE__ */ (0, x.jsx)(Af, {
				type: "submit",
				disabled: !e.available,
				...Yh(c.busy === "save"),
				children: "保存配置"
			}) })
		]
	});
}
//#endregion
//#region src/react/boardui/components/base/checkbox/checkbox-glyph.tsx
var Qh = {
	md: {
		box: "size-4",
		glyph: "size-4",
		label: "text-body-medium",
		gap: "gap-2"
	},
	sm: {
		box: "size-3.5",
		glyph: "size-3.5",
		label: "text-body-2-medium",
		gap: "gap-1.5"
	}
};
function $h({ state: e, size: t = "md" }) {
	let { isSelected: n, isIndeterminate: r, isFocusVisible: i, isDisabled: a, isHovered: o } = e, s = Qh[t], c = n || r, l = o && !a;
	return /* @__PURE__ */ (0, x.jsx)("span", {
		"aria-hidden": !0,
		className: Gd("flex shrink-0 items-center justify-center rounded-sm", "transition-[background-color,border-color,box-shadow] duration-150 ease", s.box, c ? Gd("bg-linear-to-b shadow-checkbox-selected", l ? "from-accent-400 to-accent-500" : "from-accent-500 to-accent-600") : Gd("border bg-background-primary-default shadow-xs", l ? "border-border-checkbox-hover" : "border-border-checkbox-default"), a && "opacity-50", i && "ring-2 ring-border-focus-ring ring-offset-2"),
		children: /* @__PURE__ */ (0, x.jsx)("svg", {
			viewBox: "0 0 16 16",
			fill: "none",
			className: s.glyph,
			children: r ? /* @__PURE__ */ (0, x.jsx)("path", {
				d: "M4.5 8H8H11.5",
				stroke: "white",
				strokeWidth: "2",
				strokeLinecap: "round"
			}) : n ? /* @__PURE__ */ (0, x.jsx)("path", {
				d: "M4 7.7002L6.64645 10.3466C6.84171 10.5419 7.15829 10.5419 7.35355 10.3466L12 5.7002",
				stroke: "white",
				strokeWidth: "2",
				strokeLinecap: "round",
				strokeLinejoin: "round",
				pathLength: 1,
				className: "animate-check-draw"
			}) : null
		})
	});
}
//#endregion
//#region src/react/boardui/components/base/checkbox/checkbox.tsx
function eg({ className: e, children: t, size: n = "md", ref: r, ...i }) {
	let a = Qh[n];
	return /* @__PURE__ */ (0, x.jsx)(bp, {
		ref: r,
		...i,
		className: (t) => Gd("group inline-flex items-center select-none", a.gap, t.isDisabled ? "cursor-not-allowed" : "cursor-pointer", typeof e == "function" ? e(t) : e),
		children: (e) => /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsx)($h, {
			state: e,
			size: n
		}), t != null && /* @__PURE__ */ (0, x.jsx)("span", {
			className: Gd(a.label, "text-text-primary"),
			children: t
		})] })
	});
}
//#endregion
//#region src/react/boardui/components/base/dropdown/menu-styles.ts
var tg = [
	"max-w-[calc(100vw-32px)] overflow-y-auto",
	"rounded-2xl border border-border-button-default bg-background-primary-default p-2.5 shadow-dropdown",
	"transition duration-150 ease-out",
	"data-[entering]:opacity-0 data-[entering]:scale-95 data-[entering]:blur-[2px]",
	"data-[exiting]:opacity-0 data-[exiting]:scale-95 data-[exiting]:blur-[2px]",
	"data-[placement=bottom]:origin-top-left data-[placement=top]:origin-bottom-left",
	"data-[placement=left]:origin-right data-[placement=right]:origin-left"
].join(" "), ng = "w-[266px]", rg = "flex w-full flex-col gap-1 outline-none", ig = ["flex w-full cursor-pointer items-center gap-2 rounded-2lg p-2 text-left", "text-text-primary outline-none transition-colors"].join(" ");
//#endregion
//#region src/react/boardui/components/foundations/icons/chevrons.tsx
function ag(e) {
	return /* @__PURE__ */ (0, x.jsx)("svg", {
		viewBox: "0 0 16 16",
		fill: "none",
		"aria-hidden": !0,
		...e,
		children: /* @__PURE__ */ (0, x.jsx)("path", {
			d: "M4 7L7.29289 10.2929C7.68342 10.6834 8.31658 10.6834 8.70711 10.2929L12 7",
			stroke: "currentColor",
			strokeWidth: "2",
			strokeLinecap: "round"
		})
	});
}
//#endregion
//#region src/react/boardui/utils/use-dismiss-on-outside-press.ts
function og(e, t, n) {
	(0, b.useEffect)(() => {
		if (!e) return;
		let r = (e) => {
			let r = e.target;
			n.some((e) => e.current?.contains(r)) || t();
		};
		return document.addEventListener("pointerdown", r, !0), () => document.removeEventListener("pointerdown", r, !0);
	}, [
		e,
		t,
		n
	]);
}
function sg(e, t) {
	let n = (0, b.useRef)(!1);
	return (0, b.useEffect)(() => {
		if (!e) return;
		let r = (e) => {
			t.current?.contains(e.target) && (n.current = !0, setTimeout(() => {
				n.current = !1;
			}, 400));
		};
		return document.addEventListener("pointerdown", r, !0), () => document.removeEventListener("pointerdown", r, !0);
	}, [e, t]), (e) => e && n.current ? (n.current = !1, !1) : !0;
}
//#endregion
//#region src/react/boardui/components/base/select/select.tsx
var cg = (0, b.createContext)("md");
function lg({ className: e, triggerClassName: t, popoverClassName: n, size: r = "md", children: i, items: a, renderValue: o, ref: s, ...c }) {
	let l = (0, b.useRef)(null), u = (0, b.useRef)(null), [d, f] = (0, b.useState)(!1);
	og(d, () => f(!1), [l, u]);
	let p = sg(d, l);
	return /* @__PURE__ */ (0, x.jsx)(_h, {
		ref: s,
		...c,
		isOpen: d,
		onOpenChange: (e) => p(e) && f(e),
		className: Gd("group flex flex-col", e),
		children: ({ isOpen: e }) => /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsxs)(sp, {
			ref: l,
			className: Gd("flex w-full cursor-pointer items-center justify-between rounded-2lg", "border border-border-button-default bg-background-primary-default shadow-xs", "text-text-primary", "transition-[background-color,border-color,box-shadow,padding,font-size] duration-200 ease", "hover:bg-background-primary-hover hover:border-border-button-hover", "outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus-ring", "disabled:cursor-not-allowed disabled:bg-background-primary-disabled disabled:text-text-tertiary disabled:shadow-none", r === "sm" ? "gap-1 px-[7px] py-1 text-body-2-medium" : "gap-1.5 px-2.5 py-2 text-body-medium", t),
			children: [/* @__PURE__ */ (0, x.jsx)(xh, {
				className: Gd("flex min-w-0 items-center truncate", r === "sm" ? "gap-1" : "gap-[5px]"),
				children: o
			}), /* @__PURE__ */ (0, x.jsx)(ag, { className: Gd("shrink-0 text-text-secondary transition-transform duration-200 ease", r === "sm" ? "size-3.5" : "size-4", e && "rotate-180") })]
		}), /* @__PURE__ */ (0, x.jsx)(Zm, {
			ref: u,
			isNonModal: !0,
			offset: 4,
			className: Gd(ng, tg, "p-2", n),
			children: /* @__PURE__ */ (0, x.jsx)(Im, {
				items: a,
				className: Gd(rg, "max-h-[240px] overflow-auto"),
				children: /* @__PURE__ */ (0, x.jsx)(cg.Provider, {
					value: r,
					children: i
				})
			})
		})] })
	});
}
function ug({ className: e, children: t, ...n }) {
	let r = (0, b.useContext)(cg);
	return /* @__PURE__ */ (0, x.jsx)(Bm, {
		...n,
		className: (t) => Gd(ig, r === "sm" ? "px-2 py-1.5 text-body-2-medium" : "text-body-medium", (t.isFocused || t.isSelected) && "bg-dropdown-item-hover-background", t.isDisabled && "cursor-not-allowed text-text-disabled", typeof e == "function" ? e(t) : e),
		children: t
	});
}
//#endregion
//#region src/react/settings/media-repair.tsx
var dg = {
	status: "idle",
	stage: "",
	checked: 0,
	total: 0,
	found: 0,
	repaired: 0,
	failed: 0,
	skipped: 0,
	message: ""
}, fg = (e) => Number(e).toLocaleString();
function pg(e) {
	if (e.status === "running") {
		let t = e.total ? `${fg(e.checked)} / ${fg(e.total)}` : "准备中";
		return e.stage === "修复" && e.message ? `修复 ${t} · ${e.message}` : `${e.stage || "扫描"} ${t}`;
	}
	return e.status === "complete" && (e.repaired || e.failed) ? e.failed ? `修好 ${fg(e.repaired)} 部，${fg(e.failed)} 部修不了` : `修好 ${fg(e.repaired)} 部` : "";
}
function mg({ initial: e }) {
	let [t, n] = (0, b.useState)(e || dg), [r, i] = (0, b.useState)(!1), a = Jh(), o = t.status === "running";
	(0, b.useEffect)(() => {
		let e = new AbortController(), t, r = async () => {
			try {
				let i = await Qd("/api/media-repair", e.signal);
				if (e.signal.aborted) return;
				n(i), i.status === "running" && (t = setTimeout(r, 2e3));
			} catch {}
		};
		return t = setTimeout(r, o ? 2e3 : 0), () => {
			e.abort(), clearTimeout(t);
		};
	}, [o]);
	let s = () => void a.run("start", (e) => $d("/api/media-repair", {
		allow_metered: r,
		restart: !0
	}, "POST", e), n), c = () => void a.run("stop", (e) => $d("/api/media-repair", { stop: !0 }, "POST", e), n), l = t.total ? Math.round(t.checked / t.total * 100) : 0;
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "播放兼容修复",
		children: [/* @__PURE__ */ (0, x.jsxs)(Lh, { children: [
			/* @__PURE__ */ (0, x.jsx)(zh, { children: "有些 MP4 少了一张时间戳表，浏览器按容器给的时刻排帧，会把其中一部分丢掉，看着就是卡顿。 修好之后这类片子起播直接用原片，不再实时转码。原始文件不改动，修好的头另存在缓存里。" }),
			/* @__PURE__ */ (0, x.jsx)(eg, {
				isSelected: r,
				isDisabled: o,
				onChange: i,
				children: "连 PikPak 上的一起修（要把片子完整拉一遍，走流量）"
			}),
			o ? /* @__PURE__ */ (0, x.jsx)(af, {
				label: "修复进度",
				value: l
			}) : null,
			t.status === "complete" && !t.repaired && !t.failed ? /* @__PURE__ */ (0, x.jsx)(nf, {
				tone: "info",
				title: "没有要修的",
				children: "库里的片子都能直接播，没找到缺时间戳表的。"
			}) : null,
			a.error || t.error ? /* @__PURE__ */ (0, x.jsx)(Bh, { children: a.error || t.error }) : null
		] }), /* @__PURE__ */ (0, x.jsx)(Rh, {
			status: pg(t) ? /* @__PURE__ */ (0, x.jsx)("p", {
				role: "status",
				children: pg(t)
			}) : null,
			children: o ? /* @__PURE__ */ (0, x.jsx)(Af, {
				onClick: c,
				...Yh(a.busy === "stop"),
				children: "停止"
			}) : /* @__PURE__ */ (0, x.jsx)(Af, {
				onClick: s,
				...Yh(a.busy === "start"),
				children: "开始修复"
			})
		})]
	});
}
//#endregion
//#region src/react/settings/release-updates.tsx
var hg = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]), gg = [
	65,
	67,
	90
], _g = 120;
function vg({ initial: e, initialJob: t }) {
	let [n, r] = (0, b.useState)(e), [i, o] = (0, b.useState)(t || {
		state: "idle",
		progress: 0
	}), [s, c] = (0, b.useState)(""), l = Jh(), u = (0, b.useRef)(!1), d = (0, b.useRef)(!0), f = hg.has(i.state);
	(0, b.useEffect)(() => (d.current = !0, () => {
		d.current = !1;
	}), []);
	let p = async () => {
		let e = await $d("/api/configuration/update-restart", {});
		d.current && o(e);
	}, m = () => void a({
		title: "更新已准备好",
		body: `Peach ${i.version || ""} 将在重启后安装。`,
		confirmLabel: "立即重启",
		cancelLabel: "稍后",
		onConfirm: p
	});
	(0, b.useEffect)(() => {
		i.state !== "ready" || u.current || (u.current = !0, m());
	}, [i.state]), (0, b.useEffect)(() => {
		let e = new AbortController(), t = hg.has(i.state) ? 1e3 : 3e4, n, a = 0, s = async () => {
			try {
				let t = await Qd("/api/configuration/update-status", e.signal);
				if (e.signal.aborted) return;
				o(t), a = 0, t.state === "complete" && r((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				}));
				let n = await Qd("/api/configuration/automatic-updates", e.signal);
				!e.signal.aborted && n.result && r(n.result);
			} catch {
				a += 1, a >= _g && !e.signal.aborted && c("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && a < _g && (n = setTimeout(s, t));
		};
		return n = setTimeout(s, t), () => {
			e.abort(), clearTimeout(n);
		};
	}, [i.state]);
	let h = () => {
		f || (u.current = !1, c(""), l.run("download", (e) => $d("/api/configuration/update", {}, "POST", e), o));
	}, g = () => void l.run("check", (e) => Qd("/api/configuration/updates", e), r, (t) => {
		r({
			...e,
			state: "error"
		}), l.setError(Zd(t));
	}), _ = l.error || s, v = i.state === "downloading" && i.total ? `${((i.downloaded || 0) / 1048576).toFixed(1)} / ${(i.total / 1048576).toFixed(1)} MB` : `${i.progress}%`;
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "检查更新",
		children: [
			/* @__PURE__ */ (0, x.jsxs)(Uh, { children: [
				/* @__PURE__ */ (0, x.jsx)(Wh, {
					term: "当前版本",
					children: n.current_version
				}),
				/* @__PURE__ */ (0, x.jsx)(Wh, {
					term: "安装方式",
					children: n.installation
				}),
				/* @__PURE__ */ (0, x.jsx)(Wh, {
					term: "更新通道",
					children: n.channel
				}),
				/* @__PURE__ */ (0, x.jsx)(Wh, {
					term: "最新版本",
					children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得")
				})
			] }),
			/* @__PURE__ */ (0, x.jsxs)(Lh, {
				divided: !0,
				children: [
					n.checked_at ? /* @__PURE__ */ (0, x.jsxs)(zh, { children: ["检查于 ", (/* @__PURE__ */ new Date(n.checked_at * 1e3)).toLocaleString()] }) : null,
					n.state === "available" && !_ ? /* @__PURE__ */ (0, x.jsx)(nf, {
						tone: "info",
						title: "有可用更新",
						children: n.message
					}) : _ || n.state === "error" ? /* @__PURE__ */ (0, x.jsx)(Bh, { children: _ || n.message }) : /* @__PURE__ */ (0, x.jsx)(zh, {
						role: "status",
						children: n.message
					}),
					i.state === "error" ? /* @__PURE__ */ (0, x.jsx)(Bh, { children: i.message }) : null,
					i.state !== "idle" && i.state !== "error" ? /* @__PURE__ */ (0, x.jsxs)("div", {
						"aria-live": "polite",
						className: "flex flex-col gap-2",
						children: [
							/* @__PURE__ */ (0, x.jsx)(af, {
								label: "更新准备进度：下载、校验、解压、准备安装",
								value: i.progress,
								stops: gg
							}),
							/* @__PURE__ */ (0, x.jsxs)(zh, { children: ["下载 → 校验 → 解压 → 准备安装 · ", i.message] }),
							/* @__PURE__ */ (0, x.jsx)(zh, { children: v })
						]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, x.jsxs)(Rh, {
				status: /* @__PURE__ */ (0, x.jsx)(Hh, {
					href: n.release_url,
					children: "查看发布页"
				}),
				children: [
					i.state === "ready" ? /* @__PURE__ */ (0, x.jsx)(Af, {
						onClick: m,
						children: "重启安装"
					}) : null,
					n.state === "available" && n.installation === "独立测试包" && i.state !== "ready" ? /* @__PURE__ */ (0, x.jsx)(Af, {
						onClick: h,
						...Yh(f || l.busy === "download"),
						children: "下载并安装"
					}) : null,
					/* @__PURE__ */ (0, x.jsx)(Af, {
						disabled: f,
						onClick: g,
						...Yh(l.busy === "check"),
						children: "检查更新"
					})
				]
			})
		]
	});
}
//#endregion
//#region src/react/settings/maintenance-settings.tsx
var yg = [
	["6", "每 6 小时"],
	["24", "每天"],
	["168", "每周"]
];
function bg({ data: e, receipt: t }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "flex flex-col gap-6",
		children: [
			e.automatic_updates ? /* @__PURE__ */ (0, x.jsx)(xg, {
				initial: e.automatic_updates,
				receipt: t
			}) : null,
			e.updates ? /* @__PURE__ */ (0, x.jsx)(vg, {
				initial: e.updates,
				initialJob: e.update_job
			}) : null,
			/* @__PURE__ */ (0, x.jsx)(mg, {}),
			/* @__PURE__ */ (0, x.jsx)(Sg, { facts: e.facts }),
			e.uninstall ? /* @__PURE__ */ (0, x.jsx)(Cg, { uninstall: e.uninstall }) : null
		]
	});
}
function xg({ initial: e, receipt: t }) {
	let [n, r] = (0, b.useState)(e.mode), [i, a] = (0, b.useState)(e.interval_hours), o = Jh(e.error), s = (r) => {
		r.preventDefault(), e.available && o.run("save", (e) => $d("/api/configuration/automatic-updates", {
			mode: n,
			interval_hours: i
		}, "POST", e), () => t("已保存配置"));
	}, c = e.available ? e.download_available ? "开启后一分钟内开始检查。下载完成后，在此确认重启安装。" : "开启后一分钟内开始检查。源码运行请前往发布页获取新版本。" : "自动更新需要由托盘管理的服务。";
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "自动更新",
		onSubmit: s,
		children: [
			/* @__PURE__ */ (0, x.jsxs)(Ih, { children: [
				/* @__PURE__ */ (0, x.jsx)(Bf, {
					label: "自动检查新版本",
					children: /* @__PURE__ */ (0, x.jsx)(Mh, {
						"aria-label": "自动检查新版本",
						isSelected: n !== "off",
						isDisabled: !e.available,
						onChange: (e) => r(e ? "check" : "off")
					})
				}),
				/* @__PURE__ */ (0, x.jsx)(Bf, {
					label: "自动下载更新",
					children: /* @__PURE__ */ (0, x.jsx)(Mh, {
						"aria-label": "自动下载更新",
						isSelected: n === "download",
						isDisabled: !e.available || !e.download_available || n === "off",
						onChange: (e) => r(e ? "download" : "check")
					})
				}),
				/* @__PURE__ */ (0, x.jsx)(Bf, {
					label: "检查频率",
					description: c,
					children: /* @__PURE__ */ (0, x.jsx)(lg, {
						"aria-label": "检查频率",
						selectedKey: String(i),
						isDisabled: !e.available,
						onSelectionChange: (e) => {
							e !== null && a(Number(e));
						},
						children: yg.map(([e, t]) => /* @__PURE__ */ (0, x.jsx)(ug, {
							id: e,
							children: t
						}, e))
					})
				})
			] }),
			o.error ? /* @__PURE__ */ (0, x.jsx)(Lh, {
				divided: !0,
				children: /* @__PURE__ */ (0, x.jsx)(Bh, { children: o.error })
			}) : null,
			/* @__PURE__ */ (0, x.jsx)(Rh, { children: /* @__PURE__ */ (0, x.jsx)(Af, {
				type: "submit",
				disabled: !e.available,
				...Yh(o.busy === "save"),
				children: "保存配置"
			}) })
		]
	});
}
function Sg({ facts: e }) {
	return /* @__PURE__ */ (0, x.jsx)(Fh, {
		title: "运行信息",
		children: /* @__PURE__ */ (0, x.jsx)(Uh, { children: e.map((e) => /* @__PURE__ */ (0, x.jsxs)(Wh, {
			term: e.term,
			children: [e.value, e.download_url ? /* @__PURE__ */ (0, x.jsx)(Hh, {
				href: e.download_url,
				children: e.download_label
			}) : null]
		}, e.term)) })
	});
}
function Cg({ uninstall: e }) {
	let [t, n] = (0, b.useState)(!1), [r, i] = (0, b.useState)(""), o = () => void a({
		title: "卸载 Peach",
		danger: !0,
		body: t ? "将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。",
		confirmLabel: "卸载 Peach",
		onConfirm: async () => {
			let e = await $d("/api/configuration/uninstall", {
				delete_data: t,
				confirmation: "卸载 Peach"
			});
			i(e.message);
		}
	}), s = r || e.message, c = [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])];
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		id: "uninstallPeach",
		title: "卸载 Peach",
		children: [/* @__PURE__ */ (0, x.jsxs)(Lh, { children: [
			e.available ? /* @__PURE__ */ (0, x.jsx)(zh, { children: "卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。" }) : null,
			/* @__PURE__ */ (0, x.jsx)(eg, {
				isSelected: t,
				isDisabled: !e.full_available || !!r,
				onChange: n,
				children: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存"
			}),
			/* @__PURE__ */ (0, x.jsx)(Gh, {
				summary: "数据目录",
				children: c.map((e) => /* @__PURE__ */ (0, x.jsx)("p", {
					className: "text-body-2-regular break-all text-text-secondary",
					children: e
				}, e))
			})
		] }), /* @__PURE__ */ (0, x.jsx)(Rh, {
			status: s ? /* @__PURE__ */ (0, x.jsx)("p", {
				role: r ? "status" : void 0,
				children: s
			}) : null,
			children: /* @__PURE__ */ (0, x.jsx)(Af, {
				variant: "danger",
				disabled: !e.available || !!r,
				onClick: o,
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/react/boardui/components/base/buttons/icon-button.tsx
var wg = Kd({
	base: [
		"relative inline-flex shrink-0 items-center justify-center overflow-visible rounded-2lg",
		"bg-background-primary-default text-foreground-icon-primary",
		"border border-border-button-default shadow-xs",
		"select-none cursor-pointer",
		"transition-[background-color,border-color,box-shadow,color] duration-150 ease",
		"outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus-ring",
		"hover:bg-background-primary-hover hover:border-border-button-hover",
		"active:bg-background-primary-active active:border-border-button-active",
		"disabled:cursor-not-allowed disabled:bg-background-primary-disabled disabled:border-border-button-default disabled:text-icon-button-disabled-foreground disabled:opacity-60 disabled:shadow-none"
	].join(" "),
	size: {
		medium: "size-9",
		small: "size-8"
	},
	icon: {
		medium: "size-5 shrink-0",
		small: "size-4 shrink-0"
	}
});
function Tg({ icon: e, size: t = "medium", className: n, type: r = "button", ref: i, ...a }) {
	return /* @__PURE__ */ (0, x.jsx)("button", {
		ref: i,
		type: r,
		className: Gd(wg.base, wg.size[t], n),
		...a,
		children: /* @__PURE__ */ (0, x.jsx)(e, {
			className: wg.icon[t],
			"aria-hidden": !0
		})
	});
}
//#endregion
//#region src/react/boardui/components/base/input/label.tsx
function Eg({ isRequired: e = !1, isInvalid: t, tooltip: n, className: r, children: i, ...a }) {
	return /* @__PURE__ */ (0, x.jsxs)(ip, {
		"data-label": "true",
		...a,
		className: Gd("flex cursor-default items-center gap-0.5", "text-body-medium text-text-primary", r),
		children: [
			i,
			e && /* @__PURE__ */ (0, x.jsx)("span", {
				"aria-hidden": "true",
				className: "text-body-medium text-text-error-primary",
				children: "*"
			}),
			n && /* @__PURE__ */ (0, x.jsx)(pu, {
				className: "size-4 shrink-0 text-foreground-icon-quaternary",
				"aria-hidden": !0
			})
		]
	});
}
//#endregion
//#region src/react/boardui/components/base/input/hint-text.tsx
function Dg({ isInvalid: e = !1, className: t, ...n }) {
	return /* @__PURE__ */ (0, x.jsx)(pp, {
		slot: e ? "errorMessage" : "description",
		...n,
		className: Gd("pt-px text-caption-1-medium text-text-secondary", e && "text-text-error-primary", t)
	});
}
//#endregion
//#region src/react/boardui/components/base/input/input.tsx
var Og = (0, b.createContext)({});
function kg({ size: e = "medium", fieldClassName: t, inputClassName: n, className: r, children: i, ...a }) {
	return /* @__PURE__ */ (0, x.jsx)(Og.Provider, {
		value: {
			size: e,
			fieldClassName: t,
			inputClassName: n
		},
		children: /* @__PURE__ */ (0, x.jsx)(kh, {
			...a,
			"data-input-size": e,
			className: Gd("group flex h-max w-full flex-col items-start gap-1", r),
			children: i
		})
	});
}
kg.displayName = "TextField";
var Ag = Kd({
	field: [
		"relative flex w-full items-center",
		"rounded-2lg",
		"bg-background-tertiary-default text-foreground-icon-tertiary",
		"ring-2 ring-inset ring-transparent",
		"transition-[background-color,box-shadow,color] duration-[var(--input-transition-ms)] ease"
	].join(" "),
	fieldSize: {
		medium: "p-2",
		small: "h-8 px-1.5 py-2"
	},
	fieldWithAddonSize: {
		medium: "h-9 pl-1 pr-2 py-2",
		small: "h-8 pl-1 pr-1.5 py-2"
	},
	content: "flex w-full items-center gap-2 min-w-0",
	leftSection: "flex flex-1 items-center gap-0.5 min-w-0",
	input: [
		"min-w-0 flex-1 bg-transparent border-0 outline-none p-0 m-0",
		"font-sans text-body-regular text-text-primary pl-1",
		"placeholder:text-text-tertiary",
		"focus:placeholder:text-text-primary",
		"disabled:text-input-disabled-text disabled:placeholder:text-input-disabled-text",
		"disabled:cursor-not-allowed",
		"aria-invalid:placeholder:text-text-error-placeholder"
	].join(" "),
	icon: "size-5 shrink-0"
});
function jg({ size: e, leadingIcon: t, trailingIcon: n, leadingAddon: r, fieldClassName: i, className: a, ref: o, groupRef: s, ...c }) {
	let l = (0, b.useContext)(Og), u = e ?? l.size ?? "medium", d = r != null;
	return /* @__PURE__ */ (0, x.jsx)(Cp, {
		ref: s,
		className: ({ isFocusWithin: e, isHovered: t, isDisabled: n, isInvalid: r }) => Gd(Ag.field, d ? Ag.fieldWithAddonSize[u] : Ag.fieldSize[u], t && !e && !n && !r && "ring-border-button-hover", e && !n && !r && "ring-border-button-active", n && "bg-input-disabled-background text-input-disabled-foreground", r && "bg-background-tertiary-error text-foreground-icon-error", l.fieldClassName, i),
		children: /* @__PURE__ */ (0, x.jsxs)("div", {
			className: Ag.content,
			children: [/* @__PURE__ */ (0, x.jsxs)("div", {
				className: Ag.leftSection,
				children: [d ? r : t ? /* @__PURE__ */ (0, x.jsx)(t, {
					className: Ag.icon,
					"aria-hidden": !0
				}) : null, /* @__PURE__ */ (0, x.jsx)(Ep, {
					ref: o,
					...c,
					className: Gd(Ag.input, l.inputClassName, a)
				})]
			}), n ? /* @__PURE__ */ (0, x.jsx)(n, {
				className: Ag.icon,
				"aria-hidden": !0
			}) : null]
		})
	});
}
jg.displayName = "InputBase";
function Mg({ label: e, hint: t, tooltip: n, placeholder: r, leadingIcon: i, trailingIcon: a, leadingAddon: o, fieldClassName: s, ref: c, groupRef: l, className: u, ...d }) {
	return /* @__PURE__ */ (0, x.jsx)(kg, {
		...d,
		className: u,
		"aria-label": d["aria-label"] ?? (!e && typeof r == "string" ? r : void 0),
		children: ({ isRequired: u, isInvalid: d }) => /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [
			e && /* @__PURE__ */ (0, x.jsx)(Eg, {
				isRequired: u,
				isInvalid: d,
				tooltip: n,
				children: e
			}),
			/* @__PURE__ */ (0, x.jsx)(jg, {
				ref: c,
				groupRef: l,
				placeholder: r,
				leadingIcon: i,
				trailingIcon: a,
				leadingAddon: o,
				fieldClassName: s
			}),
			t && /* @__PURE__ */ (0, x.jsx)(Dg, {
				isInvalid: d,
				children: t
			})
		] })
	});
}
Mg.displayName = "Input";
//#endregion
//#region src/configuration-endpoints.ts
var Ng = "/api/configuration", Pg = "/api/pick-folder", Fg = [
	{
		name: "机械硬盘，或内存 8 GB 以内",
		cache: "10–20 GiB",
		read: "256 / 128 KB",
		task: "1 个"
	},
	{
		name: "SATA SSD，内存 8–16 GB",
		cache: "20–50 GiB",
		read: "256 / 128 KB",
		task: "1–2 个"
	},
	{
		name: "NVMe SSD，内存 16 GB 以上",
		cache: "50–100 GiB",
		read: "256 / 128 KB",
		task: "2 个起步"
	}
], Ig = [
	["cache", "缓存上限"],
	["read", "读取长度（默认 / 最小）"],
	["task", "同时处理视频"]
];
function Lg() {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "@container flex flex-col gap-3",
		children: [/* @__PURE__ */ (0, x.jsxs)(zh, { children: ["先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。", /* @__PURE__ */ (0, x.jsx)(Hh, {
			href: "https://www.clouddrive2.com/help.html",
			children: "挂载帮助"
		})] }), /* @__PURE__ */ (0, x.jsxs)(Gh, {
			summary: "CloudDrive 缓存建议",
			children: [
				/* @__PURE__ */ (0, x.jsx)(zh, { children: "看缓存放在哪块硬盘上，照那一档填。这是起步值，填得越大不一定越快。" }),
				/* @__PURE__ */ (0, x.jsx)("ul", {
					"aria-label": "按缓存所在硬盘分档",
					className: "flex flex-col gap-2",
					children: Fg.map((e) => /* @__PURE__ */ (0, x.jsxs)("li", {
						className: "flex flex-col gap-2 rounded-2lg border border-separator-border bg-background-primary-default p-3",
						children: [/* @__PURE__ */ (0, x.jsx)("p", {
							className: "text-body-medium text-text-primary",
							children: e.name
						}), /* @__PURE__ */ (0, x.jsx)("dl", {
							className: "inline-grid grid-cols-1 gap-2 @md:grid-cols-3",
							children: Ig.map(([t, n]) => /* @__PURE__ */ (0, x.jsxs)("div", {
								className: "flex flex-col",
								children: [/* @__PURE__ */ (0, x.jsx)("dt", {
									className: "text-caption-1-regular text-text-secondary",
									children: n
								}), /* @__PURE__ */ (0, x.jsx)("dd", {
									className: "text-body-regular text-text-primary",
									children: e[t]
								})]
							}, t))
						})]
					}, e.name))
				}),
				/* @__PURE__ */ (0, x.jsxs)("ul", {
					className: "flex list-disc flex-col gap-1 pl-5 text-body-2-regular text-text-secondary",
					children: [
						/* @__PURE__ */ (0, x.jsx)("li", { children: "缓存上限和清理方式填在 CloudDrive「设置」里，清理方式选 LRU。上限不要填 0，系统盘至少留 40 GiB；填完重开设置页确认存住了。" }),
						/* @__PURE__ */ (0, x.jsx)("li", { children: "读取长度和下载线程填在每个网盘各自的下载设置里，线程都从 2 开始。" }),
						/* @__PURE__ */ (0, x.jsx)("li", { children: "Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，改一个管不住另外两个。" })
					]
				}),
				/* @__PURE__ */ (0, x.jsxs)(zh, { children: [
					"三处缓存分别管什么、这几个值怎么往上调、码率和速度怎么换算、线程上限与直链代理怎么取舍，以及这些起步值的来源，都在",
					/* @__PURE__ */ (0, x.jsx)(Hh, {
						href: "https://github.com/longmeidao/peach/blob/master/docs/CLOUDDRIVE.md",
						children: "CloudDrive 配置与调优"
					}),
					"。"
				] })
			]
		})]
	});
}
//#endregion
//#region src/react/settings/library-icon-picker.tsx
var Rg = [
	["", "自动识别"],
	["hard-drive", "磁盘"],
	["database", "资料库"],
	["heart", "心动"],
	["heart-hand", "亲密"],
	["flame", "热情"],
	["cherry", "樱桃"],
	["lollipop", "甜心"],
	["candy", "糖果"],
	["banana", "香蕉"],
	["droplets", "湿润"],
	["venus", "女性"],
	["mars", "男性"],
	["venus-and-mars", "情侣"],
	["gem", "精选"],
	["crown", "女王"],
	["ribbon", "丝带"],
	["shirt", "制服"],
	["graduation-cap", "学生"],
	["stethoscope", "护士"],
	["glasses", "眼镜"],
	["footprints", "足迹"],
	["hand", "手部"],
	["flower", "花朵"],
	["venetian-mask", "角色扮演"],
	["rabbit", "兔女郎"],
	["paw-print", "兽耳"],
	["dumbbell", "健身"],
	["bed-double", "卧室"],
	["bath", "浴室"],
	["key-round", "私密"],
	["wine", "微醺"],
	["cigarette", "烟"],
	["moon", "夜色"],
	["sparkles", "幻想"],
	["camera", "写真"],
	["video", "影片"],
	["film", "电影"],
	["image", "图集"],
	["gamepad-2", "游戏"],
	["star", "收藏"],
	["tags", "主题"]
];
function zg(e) {
	let t = e === "local" ? "" : i[e];
	return t ? [t, "自动识别"] : ["hard-drive", "默认"];
}
var Bg = "auto";
function Vg({ value: e, label: t, kind: n = "local", onChange: r }) {
	let i = (0, b.useRef)(null), [a, o] = (0, b.useState)(!1), [s, c] = (0, b.useState)(e), [l, u] = zg(n);
	return /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsx)(Af, {
		ref: i,
		variant: "secondary",
		className: "self-start",
		"aria-label": t,
		"aria-haspopup": "dialog",
		"aria-expanded": a,
		onClick: () => {
			c(e), o(!0);
		},
		children: /* @__PURE__ */ (0, x.jsxs)("span", {
			"data-icon-choice": !0,
			className: "flex items-center gap-2",
			children: [/* @__PURE__ */ (0, x.jsx)(qh, { mark: e || l }), ((e) => e && Rg.find(([t]) => t === e)?.[1] || u)(e)]
		})
	}), /* @__PURE__ */ (0, x.jsx)(Zm, {
		triggerRef: i,
		isOpen: a,
		onOpenChange: o,
		placement: "bottom start",
		offset: 4,
		className: tg,
		children: /* @__PURE__ */ (0, x.jsxs)(th, {
			"aria-label": `${t}候选`,
			className: "flex w-72 flex-col gap-3 outline-none",
			children: [
				/* @__PURE__ */ (0, x.jsx)(dp, {
					slot: "title",
					className: "px-1 text-body-medium text-text-primary",
					children: "选择媒体库图标"
				}),
				/* @__PURE__ */ (0, x.jsx)(ch, {
					"aria-label": "候选图标",
					value: s || Bg,
					onChange: (e) => c(e === Bg ? "" : e),
					className: "inline-grid grid-cols-7 gap-1",
					children: Rg.map(([e, t]) => /* @__PURE__ */ (0, x.jsx)(lh, {
						value: e || Bg,
						"aria-label": e ? t : u,
						className: "flex h-10 cursor-pointer items-center justify-center rounded-lg text-foreground-icon-secondary outline-none hover:bg-dropdown-item-hover-background focus-visible:ring-2 focus-visible:ring-border-focus-ring data-selected:bg-dropdown-item-hover-background data-selected:text-text-primary",
						children: /* @__PURE__ */ (0, x.jsx)(qh, { mark: e || l })
					}, e || Bg))
				}),
				/* @__PURE__ */ (0, x.jsxs)("div", {
					className: "flex justify-end gap-2 border-t border-separator-border pt-2.5",
					children: [/* @__PURE__ */ (0, x.jsx)(Af, {
						variant: "secondary",
						onClick: () => o(!1),
						children: "取消"
					}), /* @__PURE__ */ (0, x.jsx)(Af, {
						disabled: s === e,
						onClick: () => {
							r(s), o(!1);
						},
						children: "应用"
					})]
				})
			]
		})
	})] });
}
//#endregion
//#region src/react/settings/media-settings.tsx
var Hg = 8e3;
function Ug({ className: e }) {
	return /* @__PURE__ */ (0, x.jsx)("svg", {
		"aria-hidden": !0,
		viewBox: "0 0 24 24",
		fill: "none",
		stroke: "currentColor",
		strokeWidth: 2,
		strokeLinecap: "round",
		strokeLinejoin: "round",
		className: e,
		children: /* @__PURE__ */ (0, x.jsx)("use", { href: "#i-folder-search" })
	});
}
var Wg = [
	["local", "本地磁盘"],
	["115", "CloudDrive · 115"],
	["pikpak", "CloudDrive · PikPak"]
], Gg = (e) => Wg.find(([t]) => t === e)?.[1] ?? e, Kg = (e) => i[e] || "database", qg = (e = "") => ({
	path: e,
	location: "local",
	root: "",
	library: "",
	library_icon: ""
});
function Jg(e) {
	let t = e.media_sources?.filter((e) => Wg.some(([t]) => t === e.location));
	return t?.length ? t.map((e) => ({
		path: e.path,
		location: e.location,
		root: e.root,
		library: e.library || "",
		library_icon: e.library_icon || ""
	})) : (e.media_dirs.length ? e.media_dirs : [""]).map((e) => qg(e));
}
var Yg = (e) => !(e instanceof Yd) || e.status !== 400 ? null : e.body?.errors ?? null;
function Xg({ data: e, receipt: t }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "flex flex-col gap-6",
		children: [e.editable ? /* @__PURE__ */ (0, x.jsx)(Zg, {
			data: e,
			receipt: t
		}) : /* @__PURE__ */ (0, x.jsx)(nf, {
			tone: "neutral",
			title: "只读",
			children: e.notice
		}), /* @__PURE__ */ (0, x.jsx)($g, { data: e })]
	});
}
function Zg({ data: e, receipt: t }) {
	let [n, r] = (0, b.useState)(() => Jg(e)), [i, a] = (0, b.useState)(String(e.port)), [o, s] = (0, b.useState)(!1), [c, l] = (0, b.useState)([]), [u, d] = (0, b.useState)(""), [f, p] = (0, b.useState)(""), [m, h] = (0, b.useState)(null), [g, _] = (0, b.useState)(null), [v, y] = (0, b.useState)(null), S = (0, b.useRef)(!1), C = (0, b.useRef)(e.revision), w = (0, b.useRef)([]), T = Jh();
	(0, b.useLayoutEffect)(() => {
		g !== null && (w.current[g]?.focus(), _(null));
	}, [g]), (0, b.useEffect)(() => {
		if (!m) return;
		let e = setTimeout(() => location.assign(m.url), Hg);
		return () => clearTimeout(e);
	}, [m]);
	let E = (e, t) => r((n) => n.map((n, r) => r === e ? {
		...n,
		...t
	} : n)), D = (e, t) => l((n) => {
		let r = [...n];
		for (; r.length <= e;) r.push("");
		return r[e] = t, r;
	}), O = () => {
		_(n.length), r((e) => [...e, qg()]);
	}, k = (e) => {
		r((t) => t.filter((t, n) => n !== e)), l((t) => t.filter((t, n) => n !== e));
	}, A = async (e) => {
		if (!S.current) {
			S.current = !0, y(e);
			try {
				let { path: t } = await $d(Pg, { initial: n[e]?.path ?? "" });
				t && (E(e, { path: t }), D(e, ""));
			} catch (t) {
				D(e, Zd(t));
			} finally {
				S.current = !1, y(null);
			}
		}
	}, j = (r) => {
		r.preventDefault(), p(""), T.run("save", (t) => $d(Ng, {
			revision: C.current,
			media_dirs: n.map((e) => e.path),
			...e.media_sources ? { media_sources: n } : {},
			port: i,
			scan_now: o
		}, "POST", t), (e) => {
			C.current = e.revision, l([]), d(""), t("已保存配置"), h(e);
		}, (e) => {
			let t = Yg(e);
			l(t?.media_dirs ?? []), d(t?.port ?? ""), t || p(Zd(e));
		});
	};
	if (m) return /* @__PURE__ */ (0, x.jsx)(Fh, {
		title: "这台电脑",
		children: /* @__PURE__ */ (0, x.jsx)(Lh, { children: /* @__PURE__ */ (0, x.jsxs)(nf, {
			tone: "success",
			title: "配置已保存",
			children: [
				"Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ (0, x.jsx)(Ph, {
					href: m.url,
					size: "small",
					children: "进入馆藏"
				}),
				"。"
			]
		}) })
	});
	let M = n.some((e) => e.location === "115" || e.location === "pikpak"), N = M ? (e.mount_dependencies ?? []).filter((e) => !e.available) : [];
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "这台电脑",
		onSubmit: j,
		children: [/* @__PURE__ */ (0, x.jsxs)(Lh, { children: [
			/* @__PURE__ */ (0, x.jsxs)("div", {
				className: "flex flex-col gap-3",
				children: [
					/* @__PURE__ */ (0, x.jsx)(Vh, { children: "媒体文件夹" }),
					/* @__PURE__ */ (0, x.jsx)("div", {
						role: "group",
						"aria-label": "媒体文件夹",
						className: "flex flex-col gap-3",
						children: n.map((t, r) => /* @__PURE__ */ (0, x.jsxs)("div", {
							"data-folder-row": !0,
							className: "@container flex flex-col gap-3 rounded-2lg border border-separator-border bg-background-primary-default p-3",
							children: [/* @__PURE__ */ (0, x.jsxs)("div", {
								className: "flex items-start gap-2",
								children: [
									/* @__PURE__ */ (0, x.jsx)(Mg, {
										className: "min-w-0 flex-1",
										"aria-label": `媒体文件夹 ${r + 1}`,
										placeholder: "本机文件夹路径",
										value: t.path,
										onChange: (e) => E(r, { path: e }),
										ref: (e) => {
											w.current[r] = e;
										},
										validationBehavior: "aria",
										isInvalid: !!c[r],
										hint: c[r] || void 0
									}),
									/* @__PURE__ */ (0, x.jsx)(Tg, {
										icon: Ug,
										"aria-label": "选择文件夹",
										onClick: () => void A(r),
										...Yh(v === r)
									}),
									n.length > 1 ? /* @__PURE__ */ (0, x.jsx)(Tg, {
										icon: uu,
										"aria-label": "移除这个文件夹",
										onClick: () => k(r)
									}) : null
								]
							}), /* @__PURE__ */ (0, x.jsxs)("div", {
								className: "inline-grid grid-cols-1 gap-3 @lg:grid-cols-2",
								children: [
									/* @__PURE__ */ (0, x.jsx)(Mg, {
										label: "媒体库名称",
										maxLength: 80,
										placeholder: "同名文件夹归入同一个媒体库",
										value: t.library,
										onChange: (e) => E(r, { library: e })
									}),
									/* @__PURE__ */ (0, x.jsxs)("div", {
										className: "flex flex-col gap-1.5",
										children: [/* @__PURE__ */ (0, x.jsx)(Vh, { children: "媒体库图标" }), /* @__PURE__ */ (0, x.jsx)(Vg, {
											label: `媒体库图标 ${r + 1}`,
											value: t.library_icon,
											kind: t.location,
											onChange: (e) => E(r, { library_icon: e })
										})]
									}),
									/* @__PURE__ */ (0, x.jsxs)("div", {
										className: "flex flex-col gap-1.5",
										children: [/* @__PURE__ */ (0, x.jsx)(Vh, { children: "媒体来源" }), /* @__PURE__ */ (0, x.jsx)(lg, {
											"aria-label": `媒体来源 ${r + 1}`,
											selectedKey: t.location,
											onSelectionChange: (e) => {
												e !== null && E(r, { location: String(e) });
											},
											children: Wg.map(([e, t]) => /* @__PURE__ */ (0, x.jsxs)(ug, {
												id: e,
												textValue: t,
												children: [/* @__PURE__ */ (0, x.jsx)(qh, { mark: Kg(e) }), t]
											}, e))
										})]
									}),
									e.windows === !1 ? /* @__PURE__ */ (0, x.jsx)(Mg, {
										label: "Windows 中的对应路径",
										placeholder: "例如 B:\\",
										value: t.root,
										onChange: (e) => E(r, { root: e })
									}) : null
								]
							})]
						}, r))
					}),
					/* @__PURE__ */ (0, x.jsx)(Af, {
						className: "self-start",
						onClick: O,
						children: "添加文件夹"
					})
				]
			}),
			M ? /* @__PURE__ */ (0, x.jsx)(Lg, {}) : null,
			N.map((e) => /* @__PURE__ */ (0, x.jsxs)(zh, { children: [
				"未检测到 ",
				e.name,
				"。",
				/* @__PURE__ */ (0, x.jsxs)(Hh, {
					href: e.download_url,
					children: ["下载 ", e.name]
				})
			] }, e.name)),
			e.windows === !1 ? /* @__PURE__ */ (0, x.jsx)(zh, { children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。" }) : null,
			e.port_editable === !1 ? null : /* @__PURE__ */ (0, x.jsx)(Mg, {
				id: "configPort",
				label: "本机访问端口",
				inputMode: "numeric",
				value: i,
				onChange: a,
				validationBehavior: "aria",
				isInvalid: !!u,
				hint: u || "浏览器地址里冒号后面的数字，一般不用改。"
			}),
			/* @__PURE__ */ (0, x.jsx)(eg, {
				isSelected: o,
				onChange: s,
				children: "保存后扫描并补全资料"
			}),
			f ? /* @__PURE__ */ (0, x.jsx)(nf, {
				tone: "error",
				title: "没有保存",
				children: f
			}) : null
		] }), /* @__PURE__ */ (0, x.jsx)(Rh, {
			status: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。",
			children: /* @__PURE__ */ (0, x.jsx)(Af, {
				type: "submit",
				...Yh(T.busy === "save"),
				children: "保存配置"
			})
		})]
	});
}
function Qg({ online: e }) {
	return e === !0 ? /* @__PURE__ */ (0, x.jsxs)("span", {
		"data-mount": "online",
		className: "inline-flex items-center gap-1.5 text-body-2-medium text-notification-success-foreground",
		children: [/* @__PURE__ */ (0, x.jsx)("span", {
			"aria-hidden": !0,
			className: "size-1.5 rounded-full bg-current"
		}), "在线"]
	}) : e === !1 ? /* @__PURE__ */ (0, x.jsxs)("span", {
		"data-mount": "offline",
		className: "inline-flex items-center gap-1.5 text-body-2-medium text-text-error-primary",
		children: [/* @__PURE__ */ (0, x.jsx)("span", {
			"aria-hidden": !0,
			className: "size-1.5 rounded-full bg-current"
		}), "离线"]
	}) : /* @__PURE__ */ (0, x.jsxs)("span", {
		"data-mount": "unknown",
		className: "inline-flex items-center gap-1.5 text-body-2-medium text-text-secondary",
		children: [/* @__PURE__ */ (0, x.jsx)("span", {
			"aria-hidden": !0,
			className: "size-1.5 rounded-full bg-current"
		}), "未检测"]
	});
}
function $g({ data: e }) {
	let [t, n] = (0, b.useState)(e.media_sources), r = Jh();
	return t ? /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "挂载状态",
		children: [
			/* @__PURE__ */ (0, x.jsx)(Uh, { children: t.map((e, t) => /* @__PURE__ */ (0, x.jsxs)(Wh, {
				term: /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsx)(qh, { mark: Kg(e.location) }), Gg(e.location)] }),
				children: [e.path || "未配置挂载点", /* @__PURE__ */ (0, x.jsx)(Qg, { online: e.online })]
			}, t)) }),
			r.error ? /* @__PURE__ */ (0, x.jsx)(Lh, {
				divided: !0,
				children: /* @__PURE__ */ (0, x.jsx)(Bh, { children: r.error })
			}) : null,
			/* @__PURE__ */ (0, x.jsx)(Rh, { children: /* @__PURE__ */ (0, x.jsx)(Af, {
				onClick: () => void r.run("refresh", (e) => Qd(Ng, e), (e) => n(e.media_sources)),
				...Yh(r.busy === "refresh"),
				children: "刷新挂载状态"
			}) })
		]
	}) : null;
}
//#endregion
//#region src/react/settings/access-settings.tsx
var e_ = {
	legacy: "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。",
	locked: "访问设置无法读取，请在本机检查配置文件。",
	password: "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
};
function t_({ initial: e, receipt: t }) {
	let [n, r] = (0, b.useState)(e), [i, a] = (0, b.useState)(""), [o, s] = (0, b.useState)(""), [c, l] = (0, b.useState)(""), [u, d] = (0, b.useState)(!1), [f, p] = (0, b.useState)({}), m = (0, b.useRef)(null), h = Jh(), g = (e) => {
		e.preventDefault();
		let f = {};
		if (n.mode === "password" && !i && (f.current_password = "请输入当前访问密码"), u || ((o.length < 8 || o.length > 256) && (f.password = "访问密码需为 8–256 个字符"), o !== c && (f.confirmation = "两次输入的密码不一致")), p(f), Object.keys(f).length) {
			requestAnimationFrame(() => m.current?.querySelector("input[aria-invalid=\"true\"]")?.focus());
			return;
		}
		h.run("save", (e) => $d("/api/configuration/access", {
			revision: n.revision,
			action: u ? "disable" : "set",
			confirm_disable: u,
			current_password: i,
			password: u ? "" : o,
			confirmation: u ? "" : c
		}, "POST", e), (e) => {
			r(e), a(""), s(""), l(""), d(!1), p({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存配置");
		}, (e) => {
			let t = e instanceof Yd ? e.body : null, n = t?.errors || t?.detail?.errors;
			n ? p(n) : h.setError(Zd(e));
		});
	}, _ = e_[n.mode], v = n.mode !== "locked";
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		title: "访问密码",
		onSubmit: g,
		children: [/* @__PURE__ */ (0, x.jsx)("div", {
			ref: m,
			children: /* @__PURE__ */ (0, x.jsxs)(Lh, { children: [
				_ ? /* @__PURE__ */ (0, x.jsx)(zh, { children: _ }) : null,
				n.mode === "open" ? /* @__PURE__ */ (0, x.jsx)(nf, {
					tone: "warning",
					title: "未设置访问密码",
					children: "能连接到 Peach 的设备打开地址就能看馆藏，不需要登录。"
				}) : null,
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ (0, x.jsx)(eg, {
					isSelected: u,
					onChange: d,
					children: "关闭访问密码，允许能连接到 Peach 的设备直接访问"
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ (0, x.jsx)(Mg, {
					id: "access-current",
					type: "password",
					label: "当前访问密码",
					autoComplete: "current-password",
					maxLength: 256,
					value: i,
					onChange: a,
					isRequired: !0,
					validationBehavior: "aria",
					isInvalid: !!f.current_password,
					hint: f.current_password
				}) : null,
				v ? /* @__PURE__ */ (0, x.jsxs)(x.Fragment, { children: [/* @__PURE__ */ (0, x.jsx)(Mg, {
					id: "access-password",
					type: "password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					autoComplete: "new-password",
					maxLength: 256,
					value: o,
					onChange: s,
					isDisabled: u,
					isRequired: !u,
					validationBehavior: "aria",
					isInvalid: !u && !!f.password,
					hint: u ? "关闭访问密码时无需填写。" : f.password || "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ (0, x.jsx)(Mg, {
					id: "access-confirm",
					type: "password",
					label: "确认访问密码",
					autoComplete: "new-password",
					maxLength: 256,
					value: c,
					onChange: l,
					isDisabled: u,
					isRequired: !u,
					validationBehavior: "aria",
					isInvalid: !u && !!f.confirmation,
					hint: u ? void 0 : f.confirmation
				})] }) : null,
				u ? /* @__PURE__ */ (0, x.jsx)(nf, {
					tone: "warning",
					title: "访问范围",
					children: "保存后，能连接到 Peach 的设备将直接访问馆藏。"
				}) : null,
				h.error ? /* @__PURE__ */ (0, x.jsx)(Bh, { children: h.error }) : null
			] })
		}), v ? /* @__PURE__ */ (0, x.jsx)(Rh, {
			status: "保存后立即生效。",
			children: /* @__PURE__ */ (0, x.jsx)(Af, {
				type: "submit",
				...Yh(h.busy === "save"),
				children: "保存配置"
			})
		}) : null]
	});
}
//#endregion
//#region src/react/settings/network-settings.tsx
var n_ = [
	["environment", "系统代理"],
	["direct", "直连"],
	["proxy", "自定义"]
];
function r_({ data: e, receipt: t }) {
	return /* @__PURE__ */ (0, x.jsxs)("div", {
		className: "flex flex-col gap-6",
		children: [e.peach_proxy ? /* @__PURE__ */ (0, x.jsx)(i_, {
			initial: e.peach_proxy,
			receipt: t
		}) : null, e.access ? /* @__PURE__ */ (0, x.jsx)(t_, {
			initial: e.access,
			receipt: t
		}) : null]
	});
}
function i_({ initial: e, receipt: t }) {
	let [n, r] = (0, b.useState)(e), [i, a] = (0, b.useState)(e.mode), [o, s] = (0, b.useState)(""), c = Jh();
	return /* @__PURE__ */ (0, x.jsxs)(Fh, {
		id: "peachProxy",
		title: "Peach 代理",
		onSubmit: (e) => {
			e.preventDefault(), c.run("save", (e) => $d("/api/configuration/peach-proxy", {
				mode: i,
				proxy: o
			}, "POST", e), (e) => {
				r(e), s(""), t("已保存配置");
			});
		},
		children: [
			/* @__PURE__ */ (0, x.jsx)(Ih, { children: /* @__PURE__ */ (0, x.jsx)(Bf, {
				label: "连接方式",
				description: "采集来源选择“Peach 代理”时共用此设置。",
				children: /* @__PURE__ */ (0, x.jsx)(lg, {
					"aria-label": "连接方式",
					selectedKey: i,
					onSelectionChange: (e) => {
						e !== null && a(String(e));
					},
					children: n_.map(([e, t]) => /* @__PURE__ */ (0, x.jsx)(ug, {
						id: e,
						children: t
					}, e))
				})
			}) }),
			i === "proxy" || n.needs_selection || c.error ? /* @__PURE__ */ (0, x.jsxs)(Lh, {
				divided: !0,
				children: [
					i === "proxy" ? /* @__PURE__ */ (0, x.jsx)(Mg, {
						id: "peachProxyAddress",
						type: "password",
						label: "代理地址",
						autoComplete: "off",
						value: o,
						onChange: s,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890"
					}) : null,
					n.needs_selection ? /* @__PURE__ */ (0, x.jsx)(nf, {
						tone: "warning",
						title: "需要选择连接方式",
						children: "已有来源的代理地址不同，请选择公共连接方式。"
					}) : null,
					c.error ? /* @__PURE__ */ (0, x.jsx)(Bh, { children: c.error }) : null
				]
			}) : null,
			/* @__PURE__ */ (0, x.jsx)(Rh, { children: /* @__PURE__ */ (0, x.jsx)(Af, {
				type: "submit",
				...Yh(c.busy === "save"),
				children: "保存配置"
			}) })
		]
	});
}
//#endregion
//#region src/react/entry.tsx
var a_ = null;
function o_() {
	return a_?.isConnected || (a_ = document.createElement("div"), a_.className = "peach-react", a_.dataset.reactOverlays = "", document.body.append(a_)), a_;
}
function s_(e) {
	return (t, n) => {
		let r = (0, cu.createRoot)(t), i = (t) => r.render(/* @__PURE__ */ (0, x.jsx)(w, {
			client: of,
			children: /* @__PURE__ */ (0, x.jsx)(sc, {
				getContainer: o_,
				children: /* @__PURE__ */ (0, x.jsx)(e, { ...t })
			})
		}));
		return i(n), {
			update: i,
			unmount: () => r.unmount()
		};
	};
}
var c_ = {
	activity: {
		prefetch: (e, t) => pf(t),
		mount: s_(Of)
	},
	"quality-goals": {
		prefetch: (e, t) => Pf(t),
		mount: s_(Lf)
	}
}, l_ = s_(Xh), u_ = s_(Xg), d_ = s_(r_), f_ = s_(bg);
//#endregion
export { l_ as mountGeneralSettings, f_ as mountMaintenanceSettings, u_ as mountMediaSettings, d_ as mountNetworkSettings, c_ as pages };
