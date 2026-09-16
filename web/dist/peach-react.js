import { LOC as e, fmtDur as t, fmtSize as n, requestErrorMessage as r, siteMarkUrl as i } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as a, confirmModal as o, setCollapseOpen as s } from "/js/ui-components.js";
//#region \0rolldown/runtime.js
var c = Object.create, l = Object.defineProperty, u = Object.getOwnPropertyDescriptor, d = Object.getOwnPropertyNames, f = Object.getPrototypeOf, p = Object.prototype.hasOwnProperty, m = (e, t) => () => (t || (e((t = { exports: {} }).exports, t), e = null), t.exports), h = (e, t, n, r) => {
	if (t && typeof t == "object" || typeof t == "function") for (var i = d(t), a = 0, o = i.length, s; a < o; a++) s = i[a], !p.call(e, s) && s !== n && l(e, s, {
		get: ((e) => t[e]).bind(null, s),
		enumerable: !(r = u(t, s)) || r.enumerable
	});
	return e;
}, g = (e, t, n) => (n = e == null ? {} : c(f(e)), h(t || !e || !e.__esModule || !p.call(e, "default") ? l(n, "default", {
	value: e,
	enumerable: !0
}) : n, e)), _ = /* @__PURE__ */ m(((e) => {
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
	var ee = /\/+/g;
	function j(e, t) {
		return typeof e == "object" && e && e.key != null ? A("" + e.key) : t.toString(36);
	}
	function te(e) {
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
	function M(e, r, i, a, o) {
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
				case d: return c = e._init, M(c(e._payload), r, i, a, o);
			}
		}
		if (c) return o = o(e), c = a === "" ? "." + j(e, 0) : a, C(o) ? (i = "", c != null && (i = c.replace(ee, "$&/") + "/"), M(o, r, i, "", function(e) {
			return e;
		})) : o != null && (k(o) && (o = O(o, i + (o.key == null || e && e.key === o.key ? "" : ("" + o.key).replace(ee, "$&/") + "/") + c)), r.push(o)), 1;
		c = 0;
		var l = a === "" ? "." : a + ":";
		if (C(e)) for (var u = 0; u < e.length; u++) a = e[u], s = l + j(a, u), c += M(a, r, i, s, o);
		else if (u = h(e), typeof u == "function") for (e = u.call(e), u = 0; !(a = e.next()).done;) a = a.value, s = l + j(a, u++), c += M(a, r, i, s, o);
		else if (s === "object") {
			if (typeof e.then == "function") return M(te(e), r, i, a, o);
			throw r = String(e), Error("Objects are not valid as a React child (found: " + (r === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : r) + "). If you meant to render a collection of children, use an array instead.");
		}
		return c;
	}
	function ne(e, t, n) {
		if (e == null) return e;
		var r = [], i = 0;
		return M(e, r, "", "", function(e) {
			return t.call(n, e, i++);
		}), r;
	}
	function N(e) {
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
	var re = typeof reportError == "function" ? reportError : function(e) {
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
	function P(e) {
		var t = T.T, n = {};
		n.types = t === null ? null : t.types, T.T = n;
		try {
			var r = e(), i = T.S;
			i !== null && i(n, r), typeof r == "object" && r && typeof r.then == "function" && r.then(w, re);
		} catch (e) {
			re(e);
		} finally {
			t !== null && n.types !== null && (t.types = n.types), T.T = t;
		}
	}
	function ie(e) {
		var t = T.T;
		if (t !== null) {
			var n = t.types;
			n === null ? t.types = [e] : n.indexOf(e) === -1 && n.push(e);
		} else P(ie.bind(null, e));
	}
	var ae = {
		map: ne,
		forEach: function(e, t, n) {
			ne(e, function() {
				t.apply(this, arguments);
			}, n);
		},
		count: function(e) {
			var t = 0;
			return ne(e, function() {
				t++;
			}), t;
		},
		toArray: function(e) {
			return ne(e, function(e) {
				return e;
			}) || [];
		},
		only: function(e) {
			if (!k(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	};
	e.Activity = f, e.Children = ae, e.Component = y, e.Fragment = r, e.Profiler = a, e.PureComponent = x, e.StrictMode = i, e.Suspense = l, e.ViewTransition = p, e.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE = T, e.__COMPILER_RUNTIME = {
		__proto__: null,
		c: function(e) {
			return T.H.useMemoCache(e);
		}
	}, e.addTransitionType = ie, e.cache = function(e) {
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
			_init: N
		};
	}, e.memo = function(e, t) {
		return {
			$$typeof: u,
			type: e,
			compare: t === void 0 ? null : t
		};
	}, e.startTransition = P, e.unstable_useCacheRefresh = function() {
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
})), v = /* @__PURE__ */ m(((e, t) => {
	t.exports = _();
})), y = /* @__PURE__ */ m(((e) => {
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
})), b = /* @__PURE__ */ m(((e, t) => {
	t.exports = y();
})), x = /* @__PURE__ */ g(v(), 1), S = b(), C = x.createContext(void 0), w = (e) => {
	let t = x.useContext(C);
	if (e) return e;
	if (!t) throw Error("No QueryClient set, use QueryClientProvider to set one");
	return t;
}, T = ({ client: e, children: t }) => (x.useEffect(() => (e.mount(), () => {
	e.unmount();
}), [e]), /* @__PURE__ */ (0, S.jsx)(C.Provider, {
	value: e,
	children: t
})), E = {
	setTimeout: (e, t) => setTimeout(e, t),
	clearTimeout: (e) => clearTimeout(e),
	setInterval: (e, t) => setInterval(e, t),
	clearInterval: (e) => clearInterval(e)
}, D = new class {
	#e = E;
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
function O(e) {
	setTimeout(e, 0);
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/utils.js
var k = typeof window > "u" || "Deno" in globalThis;
function A() {}
function ee(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function j(e) {
	return typeof e == "number" && e >= 0 && e !== Infinity;
}
function te(e, t) {
	return Math.max(e + (t || 0) - Date.now(), 0);
}
function M(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function ne(e, t) {
	let { type: n = "all", exact: r, fetchStatus: i, predicate: a, queryKey: o, stale: s } = e;
	if (o) {
		if (r) {
			if (t.queryHash !== re(o, t.options)) return !1;
		} else if (!ie(t.queryKey, o)) return !1;
	}
	if (n !== "all") {
		let e = t.isActive();
		if (n === "active" && !e || n === "inactive" && e) return !1;
	}
	return !(typeof s == "boolean" && t.isStale() !== s || i && i !== t.state.fetchStatus || a && !a(t));
}
function N(e, t) {
	let { exact: n, status: r, predicate: i, mutationKey: a } = e;
	if (a) {
		if (!t.options.mutationKey) return !1;
		if (n) {
			if (P(t.options.mutationKey) !== P(a)) return !1;
		} else if (!ie(t.options.mutationKey, a)) return !1;
	}
	return !(r && t.state.status !== r || i && !i(t));
}
function re(e, t) {
	return (t?.queryKeyHashFn || P)(e);
}
function P(e) {
	return JSON.stringify(e, (e, t) => le(t) ? Object.keys(t).sort().reduce((e, n) => (e[n] = t[n], e), {}) : t);
}
function ie(e, t) {
	if (e === t) return !0;
	if (typeof e != typeof t) return !1;
	if (e && t && typeof e == "object" && typeof t == "object") {
		if (Array.isArray(e) && Array.isArray(t)) {
			for (let n = 0; n < t.length; n++) if (!ie(e[n], t[n])) return !1;
			return !0;
		}
		let n = Object.keys(t);
		for (let r of n) if (!ie(e[r], t[r])) return !1;
		return !0;
	}
	return !1;
}
var ae = Object.prototype.hasOwnProperty;
function oe(e, t, n = 0) {
	if (e === t) return e;
	if (n > 500) return t;
	let r = ce(e) && ce(t);
	if (!r && !(le(e) && le(t))) return t;
	let i = (r ? e : Object.keys(e)).length, a = r ? t : Object.keys(t), o = a.length, s = r ? Array(o) : {}, c = 0;
	for (let l = 0; l < o; l++) {
		let o = r ? l : a[l], u = e[o], d = t[o];
		if (u === d) {
			s[o] = u, (r ? l < i : ae.call(e, o)) && c++;
			continue;
		}
		if (u === null || d === null || typeof u != "object" || typeof d != "object") {
			s[o] = d;
			continue;
		}
		let f = oe(u, d, n + 1);
		s[o] = f, f === u && c++;
	}
	return i === o && c === i ? e : s;
}
function se(e, t) {
	if (!t || Object.keys(e).length !== Object.keys(t).length) return !1;
	for (let n in e) if (e[n] !== t[n]) return !1;
	return !0;
}
function ce(e) {
	return Array.isArray(e) && e.length === Object.keys(e).length;
}
function le(e) {
	if (!ue(e)) return !1;
	let t = e.constructor;
	if (t === void 0) return !0;
	let n = t.prototype;
	return !(!ue(n) || !n.hasOwnProperty("isPrototypeOf") || Object.getPrototypeOf(e) !== Object.prototype);
}
function ue(e) {
	return Object.prototype.toString.call(e) === "[object Object]";
}
function de(e) {
	return new Promise((t) => {
		D.setTimeout(t, e);
	});
}
function fe(e, t, n) {
	return typeof n.structuralSharing == "function" ? n.structuralSharing(e, t) : n.structuralSharing === !1 ? t : oe(e, t);
}
function pe(e, t, n = 0) {
	let r = [...e, t];
	return n && r.length > n ? r.slice(1) : r;
}
function F(e, t, n = 0) {
	let r = [t, ...e];
	return n && r.length > n ? r.slice(0, -1) : r;
}
var I = Symbol();
function me(e, t) {
	return !e.queryFn && t?.initialPromise ? () => t.initialPromise : !e.queryFn || e.queryFn === I ? () => Promise.reject(/* @__PURE__ */ Error(`Missing queryFn: '${e.queryHash}'`)) : e.queryFn;
}
function he(e, t) {
	return typeof e == "function" ? e(...t) : !!e;
}
function ge(e, t, n) {
	let r = !1, i;
	return Object.defineProperty(e, "signal", {
		enumerable: !0,
		get: () => (i ??= t(), r ? i : (r = !0, i.aborted ? n() : i.addEventListener("abort", n, { once: !0 }), i))
	}), e;
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/environmentManager.js
var _e = () => k, ve = () => _e(), ye = class {
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
}, be = new class extends ye {
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
}(), xe = O;
function Se() {
	let e = [], t = 0, n = (e) => {
		e();
	}, r = (e) => {
		e();
	}, i = xe, a = (r) => {
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
var Ce = Se(), we = new class extends ye {
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
function Te(e) {
	return Math.min(1e3 * 2 ** e, 3e4);
}
function Ee(e) {
	return (e ?? "online") !== "online" || we.isOnline();
}
var De = class extends Error {
	constructor(e) {
		super("CancelledError"), this.revert = e?.revert, this.silent = e?.silent;
	}
};
function Oe(e) {
	let t = !1, n = 0, r, i = "pending", a, o, s = new Promise((e, t) => {
		a = e, o = t;
	});
	s.catch(A);
	let c = () => i !== "pending", l = (t) => {
		if (!c()) {
			let n = new De(t);
			h(n), e.onCancel?.(n);
		}
	}, u = () => {
		t = !0;
	}, d = () => {
		t = !1;
	}, f = () => be.isFocused() && (e.networkMode === "always" || we.isOnline()) && e.canRun(), p = () => Ee(e.networkMode) && e.canRun(), m = (e) => {
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
			let i = e.retry ?? (ve() ? 0 : 3), a = e.retryDelay ?? Te, o = typeof a == "function" ? a(n, r) : a, s = i === !0 || typeof i == "number" && n < i || typeof i == "function" && i(n, r);
			if (t || !s) {
				h(r);
				return;
			}
			n++, e.onFail?.(n, r), de(o).then(() => f() ? void 0 : g()).then(() => {
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
var ke = class {
	#e;
	destroy() {
		this.clearGcTimeout();
	}
	scheduleGc() {
		this.clearGcTimeout(), j(this.gcTime) && (this.#e = D.setTimeout(() => {
			this.optionalRemove();
		}, this.gcTime));
	}
	updateGcTime(e) {
		this.gcTime = Math.max(this.gcTime || 0, e ?? (ve() ? Infinity : 3e5));
	}
	clearGcTimeout() {
		this.#e !== void 0 && (D.clearTimeout(this.#e), this.#e = void 0);
	}
};
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/infiniteQueryBehavior.js
function Ae(e) {
	return { onFetch: (t, n) => {
		let r = t.options, i = t.fetchOptions?.meta?.fetchMore?.direction, a = t.state.data?.pages || [], o = t.state.data?.pageParams || [], s = {
			pages: [],
			pageParams: []
		}, c = 0, l = async () => {
			let n = !1, l = (e) => {
				ge(e, () => t.signal, () => n = !0);
			}, u = me(t.options, t.fetchOptions), d = async (e, r, i) => {
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
				})(), o = await u(a), { maxPages: s } = t.options, c = i ? F : pe;
				return {
					pages: c(e.pages, o, s),
					pageParams: c(e.pageParams, r, s)
				};
			};
			if (i && a.length) {
				let e = i === "backward", t = e ? Me : je, n = {
					pages: a,
					pageParams: o
				};
				s = await d(n, t(r, n), e);
			} else {
				let t = e ?? a.length;
				do {
					let e = c === 0 ? o[0] ?? r.initialPageParam : je(r, s);
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
function je(e, { pages: t, pageParams: n }) {
	let r = t.length - 1;
	return t.length > 0 ? e.getNextPageParam(t[r], t, n[r], n) : void 0;
}
function Me(e, { pages: t, pageParams: n }) {
	return t.length > 0 ? e.getPreviousPageParam?.(t[0], t, n[0], n) : void 0;
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/query.js
var Ne = class extends ke {
	#e;
	#t;
	#n;
	#r;
	#i;
	#a;
	#o;
	#s;
	constructor(e) {
		super(), this.#s = !1, this.#o = e.defaultOptions, this.setOptions(e.options), this.observers = [], this.#i = e.client, this.#r = this.#i.getQueryCache(), this.queryKey = e.queryKey, this.queryHash = e.queryHash, this.#t = Ie(this.options), this.state = e.state ?? this.#t, this.scheduleGc();
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
			let e = Ie(this.options);
			e.data !== void 0 && (this.setState(Fe(e.data, e.dataUpdatedAt)), this.#t = e);
		}
	}
	optionalRemove() {
		!this.observers.length && this.state.fetchStatus === "idle" && this.#r.remove(this);
	}
	setData(e, t) {
		let n = fe(this.state.data, e, this.options);
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
		return this.#a?.cancel(e), t ? t.then(A).catch(A) : Promise.resolve();
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
		return this.observers.some((e) => M(e.options.enabled, this) !== !1);
	}
	isDisabled() {
		return this.getObserversCount() > 0 ? !this.isActive() : this.options.queryFn === I || !this.isFetched();
	}
	isFetched() {
		return this.state.dataUpdateCount + this.state.errorUpdateCount > 0;
	}
	isStatic() {
		return this.getObserversCount() > 0 && this.observers.some((e) => M(e.options.staleTime, this) === "static");
	}
	isStale() {
		return this.getObserversCount() > 0 ? this.observers.some((e) => e.getCurrentResult().isStale) : this.state.data === void 0 || this.state.isInvalidated;
	}
	isStaleByTime(e = 0) {
		return this.state.data === void 0 ? !0 : e === "static" ? !1 : this.state.isInvalidated ? !0 : !te(this.state.dataUpdatedAt, e);
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
			let e = me(this.options, t), n = (() => {
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
		(this.#e === "infinite" ? Ae(this.options.pages) : this.options.behavior)?.onFetch(a, this), this.#n = this.state, (this.state.fetchStatus === "idle" || this.state.fetchMeta !== a.fetchOptions?.meta) && this.#c({
			type: "fetch",
			meta: a.fetchOptions?.meta
		});
		let o = this.#a = Oe({
			initialPromise: t?.initialPromise,
			fn: a.fetchFn,
			onCancel: (e) => {
				e instanceof De && e.revert && this.setState({
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
			if (e instanceof De) {
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
					...Pe(t.data, this.options),
					fetchMeta: e.meta ?? null
				};
				case "success":
					let n = {
						...t,
						...Fe(e.data, e.dataUpdatedAt),
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
		this.state = t(this.state), Ce.batch(() => {
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
function Pe(e, t) {
	return {
		fetchFailureCount: 0,
		fetchFailureReason: null,
		fetchStatus: Ee(t.networkMode) ? "fetching" : "paused",
		...e === void 0 && {
			error: null,
			status: "pending"
		}
	};
}
function Fe(e, t) {
	return {
		data: e,
		dataUpdatedAt: t ?? Date.now(),
		error: null,
		isInvalidated: !1,
		status: "success"
	};
}
function Ie(e) {
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
var Le = class extends ye {
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
		this.listeners.size === 1 && (this.#t.addObserver(this), ze(this.#t, this.options) ? this.#m() : this.updateResult(), this.#y());
	}
	onUnsubscribe() {
		this.hasListeners() || this.destroy();
	}
	shouldFetchOnReconnect() {
		return Be(this.#t, this.options, this.options.refetchOnReconnect);
	}
	shouldFetchOnWindowFocus() {
		return Be(this.#t, this.options, this.options.refetchOnWindowFocus);
	}
	destroy() {
		this.listeners = /* @__PURE__ */ new Set(), this.#b(), this.#x(), this.#t.removeObserver(this);
	}
	setOptions(e) {
		let t = this.options, n = this.#t;
		if (this.options = this.#e.defaultQueryOptions(e), this.options.enabled !== void 0 && typeof this.options.enabled != "boolean" && typeof this.options.enabled != "function" && typeof M(this.options.enabled, this.#t) != "boolean") throw Error("Expected enabled to be a boolean or a callback that returns a boolean");
		this.#S(), this.#t.setOptions(this.options), t._defaulted && !se(this.options, t) && this.#e.getQueryCache().notify({
			type: "observerOptionsUpdated",
			query: this.#t,
			observer: this
		});
		let r = this.hasListeners();
		r && Ve(this.#t, n, this.options, t) && this.#m(), this.updateResult(), r && (this.#t !== n || M(this.options.enabled, this.#t) !== M(t.enabled, this.#t) || M(this.options.staleTime, this.#t) !== M(t.staleTime, this.#t)) && this.#g();
		let i = this.#_();
		r && (this.#t !== n || M(this.options.enabled, this.#t) !== M(t.enabled, this.#t) || i !== this.#f) && this.#v(i);
	}
	getOptimisticResult(e) {
		let t = this.#e.getQueryCache().build(this.#e, e), n = this.createResult(t, e);
		return se(this.getCurrentResult(), n) || (this.#r = n, this.#a = this.options, this.#i = this.#t.state), n;
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
		return e?.throwOnError || (t = t.catch(A)), t;
	}
	#h(e) {
		return !ve() && M(this.options.enabled, this.#t) !== !1 && j(e);
	}
	#g() {
		this.#b();
		let e = M(this.options.staleTime, this.#t);
		if (this.#r.isStale || !this.#h(e)) return;
		let t = te(this.#r.dataUpdatedAt, e) + 1;
		this.#u = D.setTimeout(() => {
			this.#r.isStale || this.updateResult();
		}, t);
	}
	#_() {
		return (typeof this.options.refetchInterval == "function" ? this.options.refetchInterval(this.#t) : this.options.refetchInterval) ?? !1;
	}
	#v(e) {
		this.#x(), this.#f = e, !(this.#f === 0 || !this.#h(this.#f)) && (this.#d = D.setInterval(() => {
			(this.options.refetchIntervalInBackground || be.isFocused()) && this.#m();
		}, this.#f));
	}
	#y() {
		this.#g(), this.#v(this.#_());
	}
	#b() {
		this.#u !== void 0 && (D.clearTimeout(this.#u), this.#u = void 0);
	}
	#x() {
		this.#d !== void 0 && (D.clearInterval(this.#d), this.#d = void 0);
	}
	createResult(e, t) {
		let n = this.#t, r = this.options, i = this.#r, a = this.#i, o = this.#a, s = e === n ? this.#n : e.state, { state: c } = e, l = { ...c }, u = !1, d;
		if (t._optimisticResults) {
			let i = this.hasListeners(), a = !i && ze(e, t), o = i && Ve(e, n, t, r);
			(a || o) && (l = {
				...l,
				...Pe(c.data, e.options)
			}), t._optimisticResults === "isRestoring" && (l.fetchStatus = "idle");
		}
		let { error: f, errorUpdatedAt: p, status: m } = l;
		d = l.data;
		let h = !1;
		if (t.placeholderData !== void 0 && d === void 0 && m === "pending") {
			let e;
			i?.isPlaceholderData && t.placeholderData === o?.placeholderData ? (e = i.data, h = !0) : e = typeof t.placeholderData == "function" ? t.placeholderData(this.#l?.state.data, this.#l) : t.placeholderData, e !== void 0 && (m = "success", d = fe(i?.data, e, t), u = !0);
		}
		if (t.select && d !== void 0 && !h) {
			if (i && d === a?.data && t.select === this.#s) d = this.#c;
			else try {
				this.#s = t.select, d = t.select(d), d = fe(i?.data, d, t), this.#c = d, this.#o = null;
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
			isStale: He(e, t),
			refetch: this.refetch,
			isEnabled: M(t.enabled, e) !== !1
		};
	}
	updateResult() {
		let e = this.#r, t = this.createResult(this.#t, this.options);
		if (this.#i = this.#t.state, this.#a = this.options, this.#i.data !== void 0 && (this.#l = this.#t), se(t, e)) return;
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
		Ce.batch(() => {
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
function Re(e, t) {
	return M(t.enabled, e) !== !1 && e.state.data === void 0 && (e.state.status !== "error" || M(t.retryOnMount, e) !== !1);
}
function ze(e, t) {
	return Re(e, t) || e.state.data !== void 0 && Be(e, t, t.refetchOnMount);
}
function Be(e, t, n) {
	if (M(t.enabled, e) !== !1 && M(t.staleTime, e) !== "static") {
		let r = typeof n == "function" ? n(e) : n;
		return r === "always" || r !== !1 && He(e, t);
	}
	return !1;
}
function Ve(e, t, n, r) {
	return (e !== t || M(r.enabled, e) === !1) && (!n.suspense || e.state.status !== "error") && He(e, n);
}
function He(e, t) {
	return M(t.enabled, e) !== !1 && e.isStaleByTime(M(t.staleTime, e));
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/mutation.js
var Ue = class extends ke {
	#e;
	#t;
	#n;
	#r;
	constructor(e) {
		super(), this.#e = e.client, this.mutationId = e.mutationId, this.#n = e.mutationCache, this.#t = [], this.state = e.state || We(), this.setOptions(e.options), this.scheduleGc();
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
		}, r = this.#r = Oe({
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
		this.state = t(this.state), Ce.batch(() => {
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
function We() {
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
var Ge = class extends ye {
	#e;
	#t;
	#n;
	constructor(e = {}) {
		super(), this.config = e, this.#e = /* @__PURE__ */ new Set(), this.#t = /* @__PURE__ */ new Map(), this.#n = 0;
	}
	build(e, t, n) {
		let r = new Ue({
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
		let t = Ke(e);
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
			let t = Ke(e);
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
		let t = Ke(e);
		if (typeof t == "string") {
			let n = this.#t.get(t)?.find((e) => e.state.status === "pending");
			return !n || n === e;
		}
		return !0;
	}
	runNext(e) {
		let t = Ke(e);
		return typeof t == "string" ? (this.#t.get(t)?.find((t) => t !== e && t.state.isPaused))?.continue() ?? Promise.resolve() : Promise.resolve();
	}
	clear() {
		Ce.batch(() => {
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
		return this.getAll().find((e) => N(t, e));
	}
	findAll(e = {}) {
		return this.getAll().filter((t) => N(e, t));
	}
	notify(e) {
		Ce.batch(() => {
			this.listeners.forEach((t) => {
				t(e);
			});
		});
	}
	resumePausedMutations() {
		let e = this.getAll().filter((e) => e.state.isPaused);
		return Ce.batch(() => Promise.all(e.map((e) => e.continue().catch(A))));
	}
};
function Ke(e) {
	return e.options.scope?.id;
}
//#endregion
//#region node_modules/@tanstack/query-core/build/modern/mutationObserver.js
var qe = class extends ye {
	#e;
	#t = void 0;
	#n;
	#r;
	constructor(e, t) {
		super(), this.#e = e, this.setOptions(t), this.bindMethods(), this.#i();
	}
	bindMethods() {
		this.mutate = this.mutate.bind(this), this.reset = this.reset.bind(this);
	}
	setOptions(e) {
		let t = this.options;
		this.options = this.#e.defaultMutationOptions(e), se(this.options, t) || this.#e.getMutationCache().notify({
			type: "observerOptionsUpdated",
			mutation: this.#n,
			observer: this
		}), t?.mutationKey && this.options.mutationKey && P(t.mutationKey) !== P(this.options.mutationKey) ? this.reset() : this.#n?.state.status === "pending" && this.#n.setOptions(this.options);
	}
	onSubscribe() {
		this.listeners.size === 1 && this.#n && (this.#n.addObserver(this), this.#i());
	}
	onUnsubscribe() {
		this.hasListeners() || this.#n?.removeObserver(this);
	}
	onMutationUpdate(e) {
		this.#i(), this.#a(e);
	}
	getCurrentResult() {
		return this.#t;
	}
	reset() {
		this.#n?.removeObserver(this), this.#n = void 0, this.#i(), this.#a();
	}
	mutate(e, t) {
		return this.#r = t, this.#n?.removeObserver(this), this.#n = this.#e.getMutationCache().build(this.#e, this.options), this.#n.addObserver(this), this.#n.execute(e);
	}
	#i() {
		let e = this.#n?.state ?? We();
		this.#t = {
			...e,
			isPending: e.status === "pending",
			isSuccess: e.status === "success",
			isError: e.status === "error",
			isIdle: e.status === "idle",
			mutate: this.mutate,
			reset: this.reset
		};
	}
	#a(e) {
		Ce.batch(() => {
			if (this.#r && this.hasListeners()) {
				let t = this.#t.variables, n = this.#t.context, r = {
					client: this.#e,
					meta: this.options.meta,
					mutationKey: this.options.mutationKey
				};
				if (e?.type === "success") {
					try {
						this.#r.onSuccess?.(e.data, t, n, r);
					} catch (e) {
						Promise.reject(e);
					}
					try {
						this.#r.onSettled?.(e.data, null, t, n, r);
					} catch (e) {
						Promise.reject(e);
					}
				} else if (e?.type === "error") {
					try {
						this.#r.onError?.(e.error, t, n, r);
					} catch (e) {
						Promise.reject(e);
					}
					try {
						this.#r.onSettled?.(void 0, e.error, t, n, r);
					} catch (e) {
						Promise.reject(e);
					}
				}
			}
			this.listeners.forEach((e) => {
				e(this.#t);
			});
		});
	}
}, Je = class extends ye {
	#e;
	constructor(e = {}) {
		super(), this.config = e, this.#e = /* @__PURE__ */ new Map();
	}
	build(e, t, n) {
		let r = t.queryKey, i = t.queryHash ?? re(r, t), a = this.get(i);
		return a || (a = new Ne({
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
		Ce.batch(() => {
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
		return this.getAll().find((e) => ne(t, e));
	}
	findAll(e = {}) {
		let t = this.getAll();
		return Object.keys(e).length > 0 ? t.filter((t) => ne(e, t)) : t;
	}
	notify(e) {
		Ce.batch(() => {
			this.listeners.forEach((t) => {
				t(e);
			});
		});
	}
	onFocus() {
		Ce.batch(() => {
			this.getAll().forEach((e) => {
				e.onFocus();
			});
		});
	}
	onOnline() {
		Ce.batch(() => {
			this.getAll().forEach((e) => {
				e.onOnline();
			});
		});
	}
}, Ye = class {
	#e;
	#t;
	#n;
	#r;
	#i;
	#a;
	#o;
	#s;
	constructor(e = {}) {
		this.#e = e.queryCache || new Je(), this.#t = e.mutationCache || new Ge(), this.#n = e.defaultOptions || {}, this.#r = /* @__PURE__ */ new Map(), this.#i = /* @__PURE__ */ new Map(), this.#a = 0;
	}
	mount() {
		this.#a++, this.#a === 1 && (this.#o = be.subscribe(async (e) => {
			e && (await this.resumePausedMutations(), this.#e.onFocus());
		}), this.#s = we.subscribe(async (e) => {
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
		return r === void 0 ? this.fetchQuery(e) : (e.revalidateIfStale && n.isStaleByTime(M(t.staleTime, n)) && this.prefetchQuery(t), Promise.resolve(r));
	}
	getQueriesData(e) {
		return this.#e.findAll(e).map(({ queryKey: e, state: t }) => [e, t.data]);
	}
	setQueryData(e, t, n) {
		let r = this.defaultQueryOptions({ queryKey: e }), i = this.#e.get(r.queryHash)?.state.data, a = ee(t, i);
		if (a !== void 0) return this.#e.build(this, r).setData(a, {
			...n,
			manual: !0
		});
	}
	setQueriesData(e, t, n) {
		return Ce.batch(() => this.#e.findAll(e).map(({ queryKey: e }) => [e, this.setQueryData(e, t, n)]));
	}
	getQueryState(e) {
		let t = this.defaultQueryOptions({ queryKey: e });
		return this.#e.get(t.queryHash)?.state;
	}
	removeQueries(e) {
		let t = this.#e;
		Ce.batch(() => {
			t.findAll(e).forEach((e) => {
				t.remove(e);
			});
		});
	}
	resetQueries(e, t) {
		let n = this.#e;
		return Ce.batch(() => {
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
		}, r = Ce.batch(() => this.#e.findAll(e).map((e) => e.cancel(n)));
		return Promise.all(r).then(A).catch(A);
	}
	invalidateQueries(e, t = {}) {
		return Ce.batch(() => (this.#e.findAll(e).forEach((e) => {
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
		}, r = Ce.batch(() => this.#e.findAll(e).filter((e) => !e.isDisabled() && !e.isStatic()).map((e) => {
			let t = e.fetch(void 0, n);
			return n.throwOnError || (t = t.catch(A)), e.state.fetchStatus === "paused" ? Promise.resolve() : t;
		}));
		return Promise.all(r).then(A);
	}
	async query(e) {
		let t = this.defaultQueryOptions(e);
		t.retry === void 0 && (t.retry = !1);
		let n = this.#e.build(this, t), r = n.isStaleByTime(M(t.staleTime, n)) ? await n.fetch(t) : n.state.data, i = t.select;
		return i ? i(r) : r;
	}
	fetchQuery(e) {
		let t = this.defaultQueryOptions(e);
		t.retry === void 0 && (t.retry = !1);
		let n = this.#e.build(this, t);
		return n.isStaleByTime(M(t.staleTime, n)) ? n.fetch(t) : Promise.resolve(n.state.data);
	}
	prefetchQuery(e) {
		return this.fetchQuery(e).then(A).catch(A);
	}
	infiniteQuery(e) {
		return e._type = "infinite", this.query(e);
	}
	fetchInfiniteQuery(e) {
		return e._type = "infinite", this.fetchQuery(e);
	}
	prefetchInfiniteQuery(e) {
		return this.fetchInfiniteQuery(e).then(A).catch(A);
	}
	ensureInfiniteQueryData(e) {
		return e._type = "infinite", this.ensureQueryData(e);
	}
	resumePausedMutations() {
		return we.isOnline() ? this.#t.resumePausedMutations() : Promise.resolve();
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
		this.#r.set(P(e), {
			queryKey: e,
			defaultOptions: t
		});
	}
	getQueryDefaults(e) {
		let t = [...this.#r.values()], n = {};
		return t.forEach((t) => {
			ie(e, t.queryKey) && Object.assign(n, t.defaultOptions);
		}), n;
	}
	setMutationDefaults(e, t) {
		this.#i.set(P(e), {
			mutationKey: e,
			defaultOptions: t
		});
	}
	getMutationDefaults(e) {
		let t = [...this.#i.values()], n = {};
		return t.forEach((t) => {
			ie(e, t.mutationKey) && Object.assign(n, t.defaultOptions);
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
		return t.queryHash ||= re(t.queryKey, t), t.refetchOnReconnect === void 0 && (t.refetchOnReconnect = t.networkMode !== "always"), t.throwOnError === void 0 && (t.throwOnError = !!t.suspense), !t.networkMode && t.persister && (t.networkMode = "offlineFirst"), t.queryFn === I && (t.enabled = !1), t;
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
}, Xe = x.createContext(!1), Ze = () => x.useContext(Xe);
Xe.Provider;
//#endregion
//#region node_modules/@tanstack/react-query/build/modern/QueryErrorResetBoundary.js
function Qe() {
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
var $e = x.createContext(Qe()), et = () => x.useContext($e), tt = (e, t, n) => {
	let r = n?.state.error && typeof e.throwOnError == "function" ? he(e.throwOnError, [n.state.error, n]) : e.throwOnError;
	(e.suspense || r) && (t.isReset() || (e.retryOnMount = !1));
}, nt = (e) => {
	x.useEffect(() => {
		e.clearReset();
	}, [e]);
}, rt = ({ result: e, errorResetBoundary: t, throwOnError: n, query: r, suspense: i }) => e.isError && !t.isReset() && !e.isFetching && r && (i && e.data === void 0 || he(n, [e.error, r])), it = (e) => {
	if (e.suspense) {
		let t = 1e3, n = (e) => e === "static" ? e : Math.max(e ?? t, t), r = e.staleTime;
		e.staleTime = typeof r == "function" ? (...e) => n(r(...e)) : n(r), typeof e.gcTime == "number" && (e.gcTime = Math.max(e.gcTime, t));
	}
}, at = (e, t) => e?.suspense && t.isPending, ot = (e, t, n) => t.fetchOptimistic(e).catch(() => {
	n.clearReset();
});
//#endregion
//#region node_modules/@tanstack/react-query/build/modern/useBaseQuery.js
function st(e, t, n) {
	let r = Ze(), i = et(), a = w(n), o = a.defaultQueryOptions(e), s = a.getQueryCache().get(o.queryHash), c = e.subscribed !== !1;
	o._optimisticResults = r ? "isRestoring" : c ? "optimistic" : void 0, it(o), tt(o, i, s), nt(i);
	let [l] = x.useState(() => new t(a, o)), u = l.getOptimisticResult(o), d = !r && c;
	if (x.useSyncExternalStore(x.useCallback((e) => {
		let t = d ? l.subscribe(Ce.batchCalls(e)) : A;
		return l.updateResult(), t;
	}, [l, d]), () => l.getCurrentResult(), () => l.getCurrentResult()), x.useEffect(() => {
		l.setOptions(o);
	}, [o, l]), at(o, u)) throw ot(o, l, i);
	if (rt({
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
function ct(e, t) {
	return st(e, Le, t);
}
//#endregion
//#region node_modules/@tanstack/react-query/build/modern/useMutation.js
function lt(e, t) {
	let n = w(t), [r] = x.useState(() => new qe(n, e));
	x.useEffect(() => {
		r.setOptions(e);
	}, [r, e]);
	let i = x.useSyncExternalStore(x.useCallback((e) => r.subscribe(Ce.batchCalls(e)), [r]), () => r.getCurrentResult(), () => r.getCurrentResult()), a = x.useCallback((...e) => {
		r.mutate(e[0], e[1]).catch(A);
	}, [r]);
	if (i.error && he(r.options.throwOnError, [i.error])) throw i.error;
	return {
		...i,
		mutate: a,
		mutateAsync: i.mutate
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/collections/BaseCollection.mjs
var ut = class {
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
}, dt = class extends ut {
	filter(e, t, n) {
		let [r, i] = ht(e, t, this.firstChildKey, n), a = this.clone();
		return a.firstChildKey = r, a.lastChildKey = i, a;
	}
};
(class extends ut {
	static {
		this.type = "header";
	}
});
var ft = class extends ut {
	static {
		this.type = "loader";
	}
}, pt = class extends dt {
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
(class extends dt {
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
var mt = class {
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
		let t = new this.constructor(), [n, r] = ht(this, t, this.firstKey, e);
		return t?.commit(n, r), t;
	}
	constructor() {
		this.keyMap = /* @__PURE__ */ new Map(), this.firstKey = null, this.lastKey = null, this.frozen = !1, this.itemCount = 0;
	}
};
function ht(e, t, n, r) {
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
var gt = class {
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
}, _t = class e extends gt {
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
}, vt = class extends gt {
	constructor(e) {
		super(null), this.nodeType = 11, this.ownerDocument = this, this.dirtyNodes = /* @__PURE__ */ new Set(), this.isSSR = !1, this.nodeId = 0, this.nodesByProps = /* @__PURE__ */ new WeakMap(), this.nextCollection = null, this.subscriptions = /* @__PURE__ */ new Set(), this.queuedRender = !1, this.inSubscription = !1, this.collection = e, this.nextCollection = e;
	}
	get isConnected() {
		return !0;
	}
	createElement(e) {
		return new _t(e, this);
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
		for (let e of this.dirtyNodes) e instanceof _t && (!e.isConnected || e.isHidden) ? this.removeNode(e) : e.updateChildIndices();
		for (let e of this.dirtyNodes) e instanceof _t ? (e.isConnected && !e.isHidden && (e.updateNode(), this.addNode(e)), e.node && this.dirtyNodes.delete(e), e.isMutated = !1) : this.dirtyNodes.delete(e);
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
function yt(e) {
	let { children: t, items: n, idScope: r, addIdAndValue: i, dependencies: a = [] } = e, o = (0, x.useMemo)(() => void 0, [t]), s = (0, x.useMemo)(() => /* @__PURE__ */ new WeakMap(), [...a, o]);
	return (0, x.useMemo)(() => {
		if (n && typeof t == "function") {
			let e = [];
			for (let a of n) {
				let n = bt(a) ? a : null, o = n ? s.get(n) : null;
				if (!o) {
					o = t(a);
					let c = o.props.id ?? a?.key ?? a?.id;
					r != null && o.props.id == null && c != null && (c = r + ":" + c);
					let l = c ?? e.length;
					o = (0, x.cloneElement)(o, i ? {
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
function bt(e) {
	switch (typeof e) {
		case "object": return e != null;
		case "function":
		case "symbol": return !0;
		default: return !1;
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/focusWithoutScrolling.mjs
function xt(e) {
	if (Ct()) e.focus({ preventScroll: !0 });
	else {
		let t = wt(e);
		e.focus(), Tt(t);
	}
}
var St = null;
function Ct() {
	if (St == null) {
		St = !1;
		try {
			document.createElement("div").focus({ get preventScroll() {
				return St = !0, !0;
			} });
		} catch {}
	}
	return St;
}
function wt(e) {
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
function Tt(e) {
	for (let { element: t, scrollTop: n, scrollLeft: r } of e) t.scrollTop = n, t.scrollLeft = r;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/domHelpers.mjs
var L = (e) => Ot(e) ? e.document : kt(e) ? e : e?.ownerDocument ?? (typeof document < "u" ? document : void 0), Et = (e) => L(e)?.defaultView ?? (typeof window < "u" ? window : void 0);
function Dt(e) {
	return typeof e == "object" && !!e && "nodeType" in e && typeof e.nodeType == "number";
}
function Ot(e) {
	return typeof e == "object" && !!e && "window" in e && e.window === e;
}
function kt(e) {
	return Dt(e) && e.nodeType === 9;
}
function At(e) {
	return Dt(e) && e.nodeType === 11 && "host" in e;
}
function jt(e, t, n, r) {
	if (n == null || e == null) return () => {};
	let i = Array.isArray(e) ? e : [e];
	for (let e of i) e.addEventListener(t, n, r);
	return () => {
		for (let e of i) e.removeEventListener(t, n, r);
	};
}
function Mt(e, t, n, r) {
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
var Nt = !1;
function Pt() {
	return Nt;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/shadowdom/DOMFunctions.mjs
function R(e, t) {
	if (!Pt()) return t && e ? e.contains(t) : !1;
	if (!e || !t) return !1;
	let n = t;
	for (; n !== null;) {
		if (n === e) return !0;
		n = typeof n.assignedElements != "function" && n.assignedSlot?.parentNode ? n.assignedSlot.parentNode : At(n) ? n.host : n.parentNode;
	}
	return !1;
}
var Ft = (e = document) => {
	if (!Pt()) return e.activeElement;
	let t = e.activeElement;
	for (; t && "shadowRoot" in t && t.shadowRoot?.activeElement;) t = t.shadowRoot.activeElement;
	return t;
};
function z(e) {
	if (Pt() && e.target instanceof Element && e.target.shadowRoot) {
		if ("composedPath" in e) return e.composedPath()[0] ?? null;
		if ("composedPath" in e.nativeEvent) return e.nativeEvent.composedPath()[0] ?? null;
	}
	return e.target;
}
function It(e, t) {
	if (t === null) return [];
	t ??= Et(e);
	let n = [t];
	if (!Pt() || !e || e === t) return n;
	let r = "getRootNode" in t ? t.getRootNode() : null, i = e.getRootNode() ?? null;
	for (; At(i) && i !== r;) n.push(i), i = i.host.getRootNode();
	return n;
}
function Lt(e) {
	if (!e) return !1;
	let t = e.getRootNode(), n = Et(e);
	if (!(t instanceof n.Document || t instanceof n.ShadowRoot)) return !1;
	let r = t.activeElement;
	return r != null && e.contains(r);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/isElementVisible.mjs
var Rt = typeof Element < "u" && "checkVisibility" in Element.prototype;
function zt(e) {
	let t = Et(e);
	if (!(e instanceof t.HTMLElement) && !(e instanceof t.SVGElement)) return !1;
	let { display: n, visibility: r } = e.style, i = n !== "none" && r !== "hidden" && r !== "collapse";
	if (i) {
		let { getComputedStyle: t } = Et(e), { display: n, visibility: r } = t(e);
		i = n !== "none" && r !== "hidden" && r !== "collapse";
	}
	return i;
}
function Bt(e, t) {
	return !e.hasAttribute("hidden") && !e.hasAttribute("data-react-aria-prevent-focus") && (e.nodeName === "DETAILS" && t && t.nodeName !== "SUMMARY" ? e.hasAttribute("open") : !0);
}
function Vt(e, t) {
	return Rt ? e.checkVisibility({ visibilityProperty: !0 }) && !e.closest("[data-react-aria-prevent-focus]") : e.nodeName !== "#comment" && zt(e) && Bt(e, t) && (!e.parentElement || Vt(e.parentElement, e));
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/isFocusable.mjs
var Ht = [
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
], B = Ht.join(":not([hidden]),") + ",[tabindex]:not([disabled]):not([hidden])";
Ht.push("[tabindex]:not([tabindex=\"-1\"]):not([disabled])");
var Ut = Ht.join(":not([hidden]):not([tabindex=\"-1\"]),");
function Wt(e, t) {
	return e.matches(B) && !Kt(e) && (t?.skipVisibilityCheck || Vt(e));
}
function Gt(e) {
	return e.matches(Ut) && Vt(e) && !Kt(e);
}
function Kt(e) {
	let t = e;
	for (; t != null;) {
		if (t instanceof Et(t).HTMLElement && t.inert) return !0;
		t = t.parentElement;
	}
	return !1;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useLayoutEffect.mjs
var V = typeof document < "u" ? x.useLayoutEffect : () => {};
//#endregion
//#region node_modules/react-aria/dist/private/interactions/utils.mjs
function qt(e) {
	let t = e;
	return t.nativeEvent = e, t.isDefaultPrevented = () => t.defaultPrevented, t.isPropagationStopped = () => t.cancelBubble, t.persist = () => {}, t;
}
function Jt(e, t) {
	Object.defineProperty(e, "target", { value: t }), Object.defineProperty(e, "currentTarget", { value: t });
}
function Yt(e) {
	let t = (0, x.useRef)({
		isFocused: !1,
		observer: null
	});
	return V(() => {
		let e = t.current;
		return () => {
			e.observer &&= (e.observer.disconnect(), null);
		};
	}, []), (0, x.useCallback)((n) => {
		let r = z(n);
		if (r instanceof HTMLButtonElement || r instanceof HTMLInputElement || r instanceof HTMLTextAreaElement || r instanceof HTMLSelectElement) {
			t.current.isFocused = !0;
			let n = r;
			n.addEventListener("focusout", (r) => {
				if (t.current.isFocused = !1, n.disabled) {
					let t = qt(r);
					e?.(t);
				}
				t.current.observer && (t.current.observer.disconnect(), t.current.observer = null);
			}, { once: !0 }), t.current.observer = new MutationObserver(() => {
				if (t.current.isFocused && n.disabled) {
					t.current.observer?.disconnect();
					let e = n === Ft() ? null : Ft();
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
var Xt = !1;
function Zt(e) {
	for (; e && !Wt(e, { skipVisibilityCheck: !0 });) e = e.parentElement;
	let t = Ft(Et(e).document);
	if (!t || t === e) return;
	let n = e?.getRootNode(), r = n != null && At(n) ? n : Et(e), i = (t) => t === e || t != null && R(e, t), a = (e) => e === t || t != null && e != null && R(t, e);
	Xt = !0;
	let o = !1, s = (e) => {
		(a(z(e)) || o) && e.stopImmediatePropagation();
	}, c = (n) => {
		(a(z(n)) || o) && (n.stopImmediatePropagation(), !e && !o && (o = !0, xt(t), d()));
	}, l = (e) => {
		(i(z(e)) || o) && e.stopImmediatePropagation();
	}, u = (e) => {
		(i(z(e)) || o) && (e.stopImmediatePropagation(), o || (o = !0, xt(t), d()));
	};
	r.addEventListener("blur", s, !0), r.addEventListener("focusout", c, !0), r.addEventListener("focusin", u, !0), r.addEventListener("focus", l, !0);
	let d = () => {
		cancelAnimationFrame(f), r.removeEventListener("blur", s, !0), r.removeEventListener("focusout", c, !0), r.removeEventListener("focusin", u, !0), r.removeEventListener("focus", l, !0), Xt = !1, o = !1;
	}, f = requestAnimationFrame(d);
	return d;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/platform.mjs
function Qt(e) {
	if (typeof window > "u" || window.navigator == null) return !1;
	let t = window.navigator.userAgentData?.brands;
	return Array.isArray(t) && t.some((t) => e.test(t.brand)) || e.test(window.navigator.userAgent);
}
function $t(e) {
	return typeof window < "u" && window.navigator != null && e.test(window.navigator.userAgentData?.platform || window.navigator.platform);
}
function en(e) {
	let t = null;
	return () => (t ??= e(), t);
}
var tn = en(function() {
	return $t(/^Mac/i);
}), nn = en(function() {
	return $t(/^iPhone/i);
}), rn = en(function() {
	return $t(/^iPad/i) || tn() && navigator.maxTouchPoints > 1;
}), an = en(function() {
	return nn() || rn();
}), on = en(function() {
	return tn() || an();
}), sn = en(function() {
	return Qt(/AppleWebKit/i) && (an() || !cn());
}), cn = en(function() {
	return Qt(/Chrome|CriOS|CrMo/i);
}), ln = en(function() {
	return Qt(/Android/i);
}), un = en(function() {
	return Qt(/(Firefox|FxiOS)/i);
});
//#endregion
//#region node_modules/react-aria/dist/private/utils/isVirtualEvent.mjs
function dn(e) {
	return e.pointerType === "" && e.isTrusted ? !0 : ln() && e.pointerType ? e.type === "click" && e.buttons === 1 : e.detail === 0 && !e.pointerType;
}
function fn(e) {
	return !ln() && e.width === 0 && e.height === 0 || ln() && e.width === 1 && e.height === 1 && e.pressure === 0 && e.detail === 0 && e.pointerType === "mouse";
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/openLink.mjs
var pn = /*#__PURE__*/ (0, x.createContext)({
	isNative: !0,
	open: _n,
	useHref: (e) => e
});
function mn() {
	return (0, x.useContext)(pn);
}
function hn(e, t, n = !0) {
	let { metaKey: r, ctrlKey: i, altKey: a, shiftKey: o } = t;
	!sn() && un() && window.event?.type?.startsWith("key") && e.target === "_blank" && (tn() ? r = !0 : i = !0);
	let s = sn() && tn() && !rn() ? new KeyboardEvent("keydown", {
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
	hn.isOpening = n, xt(e), e.dispatchEvent(s), hn.isOpening = !1;
}
hn.isOpening = !1;
function gn(e, t) {
	if (e instanceof HTMLAnchorElement) t(e);
	else if (e.hasAttribute("data-href")) {
		let n = document.createElement("a");
		n.href = e.getAttribute("data-href"), e.hasAttribute("data-target") && (n.target = e.getAttribute("data-target")), e.hasAttribute("data-rel") && (n.rel = e.getAttribute("data-rel")), e.hasAttribute("data-download") && (n.download = e.getAttribute("data-download")), e.hasAttribute("data-ping") && (n.ping = e.getAttribute("data-ping")), e.hasAttribute("data-referrer-policy") && (n.referrerPolicy = e.getAttribute("data-referrer-policy")), e.appendChild(n), t(n), e.removeChild(n);
	}
}
function _n(e, t) {
	gn(e, (e) => hn(e, t));
}
function vn(e) {
	let t = mn().useHref(e?.href ?? ""), n = {};
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
var yn = {
	prefix: String(Math.round(Math.random() * 1e10)),
	current: 0
}, bn = /*#__PURE__*/ x.createContext(yn), xn = /*#__PURE__*/ x.createContext(!1);
typeof window < "u" && window.document && window.document.createElement;
var Sn = /* @__PURE__ */ new WeakMap();
function Cn(e = !1) {
	let t = (0, x.useContext)(bn), n = (0, x.useRef)(null);
	if (n.current === null && !e) {
		let e = x.default.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED?.ReactCurrentOwner?.current;
		if (e) {
			let n = Sn.get(e);
			n == null ? Sn.set(e, {
				id: t.current,
				state: e.memoizedState
			}) : e.memoizedState !== n.state && (t.current = n.id, Sn.delete(e));
		}
		n.current = ++t.current;
	}
	return n.current;
}
function wn(e) {
	let t = (0, x.useContext)(bn), n = Cn(!!e), r = `react-aria${t.prefix}`;
	return e || `${r}-${n}`;
}
function Tn(e) {
	let t = x.useId(), [n] = (0, x.useState)(An()), r = n ? "react-aria" : `react-aria${yn.prefix}`;
	return e || `${r}-${t}`;
}
var En = typeof x.useId == "function" ? Tn : wn;
function Dn() {
	return !1;
}
function On() {
	return !0;
}
function kn(e) {
	return () => {};
}
function An() {
	return typeof x.useSyncExternalStore == "function" ? x.useSyncExternalStore(kn, Dn, On) : (0, x.useContext)(xn);
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocusVisible.mjs
var jn = null, Mn = /* @__PURE__ */ new Set(), Nn = /* @__PURE__ */ new Map(), Pn = !1, Fn = !1, In = {
	Tab: !0,
	Escape: !0
};
function Ln(e, t) {
	for (let n of Mn) n(e, t);
}
function Rn(e) {
	return !(e.metaKey || !tn() && e.altKey || e.ctrlKey || e.key === "Control" || e.key === "Shift" || e.key === "Meta");
}
function zn(e) {
	Pn = !0, !hn.isOpening && Rn(e) && (jn = "keyboard", Ln("keyboard", e));
}
function Bn(e) {
	jn = "pointer", "pointerType" in e && e.pointerType, (e.type === "mousedown" || e.type === "pointerdown") && (Pn = !0, Ln("pointer", e));
}
function Vn(e) {
	!hn.isOpening && dn(e) && (Pn = !0, jn = "virtual");
}
function Hn(e) {
	if (Xt) return;
	let t = z(e), n = Et(t), r = L(t);
	if (t === n) {
		Fn = !0;
		return;
	}
	t === r || !e.isTrusted || (!Pn && !Fn && (jn = "virtual", Ln("virtual", e)), Pn = !1, Fn = !1);
}
function Un() {
	Xt || (Pn = !1, Fn = !0);
}
function Wn(e) {
	if (typeof window > "u" || typeof document > "u") return;
	let t = Et(e), n = L(e);
	if (Nn.get(t)) return;
	let r = t.HTMLElement.prototype.focus;
	Reflect.defineProperty(t.HTMLElement.prototype, "focus", {
		configurable: !0,
		writable: !0,
		value: function() {
			Pn = !0, r.apply(this, arguments);
		}
	}), n.addEventListener("keydown", zn, !0), n.addEventListener("keyup", zn, !0), n.addEventListener("click", Vn, !0), t.addEventListener("focus", Hn, !0), t.addEventListener("blur", Un, !1), typeof PointerEvent < "u" && (n.addEventListener("pointerdown", Bn, !0), n.addEventListener("pointermove", Bn, !0), n.addEventListener("pointerup", Bn, !0)), t.addEventListener("beforeunload", () => {
		Gn(e);
	}, { once: !0 }), Nn.set(t, { focus: r });
}
var Gn = (e, t) => {
	let n = Et(e), r = L(e);
	t && r.removeEventListener("DOMContentLoaded", t), Nn.has(n) && (Reflect.defineProperty(n.HTMLElement.prototype, "focus", {
		configurable: !0,
		writable: !0,
		value: Nn.get(n).focus
	}), r.removeEventListener("keydown", zn, !0), r.removeEventListener("keyup", zn, !0), r.removeEventListener("click", Vn, !0), n.removeEventListener("focus", Hn, !0), n.removeEventListener("blur", Un, !1), typeof PointerEvent < "u" && (r.removeEventListener("pointerdown", Bn, !0), r.removeEventListener("pointermove", Bn, !0), r.removeEventListener("pointerup", Bn, !0)), Nn.delete(n));
};
function Kn(e) {
	let t = L(e), n;
	return t.readyState === "loading" ? (n = () => {
		Wn(e);
	}, t.addEventListener("DOMContentLoaded", n)) : Wn(e), () => Gn(e, n);
}
typeof document < "u" && Kn();
function qn() {
	return jn !== "pointer";
}
function Jn() {
	return jn;
}
function Yn(e) {
	jn = e, Ln(e, null);
}
var Xn = /* @__PURE__ */ new Set([
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
function Zn(e, t, n) {
	let r = n ? z(n) : void 0, i = L(r), a = Et(r), o = a === void 0 ? HTMLInputElement : a.HTMLInputElement, s = a === void 0 ? HTMLTextAreaElement : a.HTMLTextAreaElement, c = a === void 0 ? HTMLElement : a.HTMLElement, l = a === void 0 ? KeyboardEvent : a.KeyboardEvent, u = Ft(i);
	return e = e || u instanceof o && !Xn.has(u.type) || u instanceof s || u instanceof c && u.isContentEditable, !(e && t === "keyboard" && n instanceof l && !In[n.key]);
}
function Qn(e, t, n) {
	Wn(), (0, x.useEffect)(() => {
		if (n?.enabled === !1) return;
		let t = (t, r) => {
			Zn(!!n?.isTextInput, t, r) && e(qn());
		};
		return Mn.add(t), () => {
			Mn.delete(t);
		};
	}, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/runAfterTransition.mjs
var $n = /* @__PURE__ */ new Map(), er = /* @__PURE__ */ new Set();
function tr() {
	if (typeof window > "u") return;
	function e(e) {
		return "propertyName" in e;
	}
	let t = (t) => {
		let r = z(t);
		if (!e(t) || !r) return;
		let i = $n.get(r);
		i || (i = /* @__PURE__ */ new Set(), $n.set(r, i), r.addEventListener("transitioncancel", n, { once: !0 })), i.add(t.propertyName);
	}, n = (t) => {
		let r = z(t);
		if (!e(t) || !r) return;
		let i = $n.get(r);
		if (i && (i.delete(t.propertyName), i.size === 0 && (r.removeEventListener("transitioncancel", n), $n.delete(r)), $n.size === 0)) {
			for (let e of er) e();
			er.clear();
		}
	};
	document.body.addEventListener("transitionrun", t), document.body.addEventListener("transitionend", n);
}
typeof document < "u" && (document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", tr) : tr());
function nr() {
	for (let [e] of $n) "isConnected" in e && !e.isConnected && $n.delete(e);
}
function rr(e) {
	requestAnimationFrame(() => {
		nr(), $n.size === 0 ? e() : er.add(e);
	});
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/focusSafely.mjs
function ir(e) {
	if (!e.isConnected) return;
	let t = L(e);
	if (Jn() === "virtual") {
		let n = Ft(t);
		rr(() => {
			let r = Ft(t);
			(r === n || r === t.body) && e.isConnected && xt(e);
		});
	} else xt(e);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/chain.mjs
function ar(...e) {
	return (...t) => {
		for (let n of e) typeof n == "function" && n(...t);
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useValueEffect.mjs
function or(e) {
	let [t, n] = (0, x.useState)(e), r = (0, x.useRef)(t), i = (0, x.useRef)(null), a = (0, x.useRef)(() => {
		if (!i.current) return;
		let e = i.current.next();
		if (e.done) {
			i.current = null;
			return;
		}
		r.current === e.value ? a.current() : n(e.value);
	});
	return V(() => {
		r.current = t, i.current && a.current();
	}), [t, (0, x.useCallback)((e) => {
		i.current = e(r.current), a.current();
	}, [a])];
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useId.mjs
var sr = !!(typeof window < "u" && window.document && window.document.createElement), cr = /* @__PURE__ */ new Map(), lr;
typeof FinalizationRegistry < "u" && (lr = new FinalizationRegistry((e) => {
	cr.delete(e);
}));
var ur = /* @__PURE__ */ new WeakMap();
function dr(e) {
	let [t, n] = (0, x.useState)(e), r = (0, x.useRef)(null), i = En(t), a = (0, x.useRef)(null), o = ur.get(a);
	if (lr && o !== i && (o != null && lr.unregister(a), lr.register(a, i, a), ur.set(a, i)), sr) {
		let e = cr.get(i);
		e && !e.includes(r) ? e.push(r) : cr.set(i, [r]);
	}
	return V(() => {
		let e = i;
		return () => {
			lr && (lr.unregister(a), ur.delete(a)), cr.delete(e);
		};
	}, [i]), (0, x.useEffect)(() => {
		let e = r.current;
		return e && n(e), () => {
			e && (r.current = null);
		};
	}), i;
}
function fr(e, t) {
	if (e === t) return e;
	let n = cr.get(e);
	if (n) return n.forEach((e) => e.current = t), t;
	let r = cr.get(t);
	return r ? (r.forEach((t) => t.current = e), e) : t;
}
function pr(e = []) {
	let t = dr(), [n, r] = or(t), i = (0, x.useCallback)(() => {
		r(function* () {
			yield t, yield document.getElementById(t) ? t : void 0;
		});
	}, [t, r]);
	return V(i, [
		t,
		i,
		...e
	]), n;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/mergeRefs.mjs
function mr(...e) {
	return e.length === 1 && e[0] ? e[0] : (t) => {
		let n = !1, r = e.map((e) => {
			let r = hr(e, t);
			return n ||= typeof r == "function", r;
		});
		if (n) return () => {
			r.forEach((t, n) => {
				typeof t == "function" ? t() : hr(e[n], null);
			});
		};
	};
}
function hr(e, t) {
	if (typeof e == "function") return e(t);
	e != null && (e.current = t);
}
//#endregion
//#region node_modules/clsx/dist/clsx.mjs
function gr(e) {
	var t, n, r = "";
	if (typeof e == "string" || typeof e == "number") r += e;
	else if (typeof e == "object") {
		if (Array.isArray(e)) {
			var i = e.length;
			for (t = 0; t < i; t++) e[t] && (n = gr(e[t])) && (r && (r += " "), r += n);
		} else for (n in e) e[n] && (r && (r += " "), r += n);
	}
	return r;
}
function _r() {
	for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = gr(e)) && (r && (r += " "), r += t);
	return r;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/mergeProps.mjs
function H(...e) {
	let t = { ...e[0] };
	for (let n = 1; n < e.length; n++) {
		let r = e[n];
		for (let e in r) {
			let n = t[e], i = r[e];
			typeof n == "function" && typeof i == "function" && e[0] === "o" && e[1] === "n" && e.charCodeAt(2) >= 65 && e.charCodeAt(2) <= 90 ? t[e] = ar(n, i) : (e === "className" || e === "UNSAFE_className") && typeof n == "string" && typeof i == "string" ? t[e] = _r(n, i) : e === "id" && n && i ? t.id = fr(n, i) : e === "ref" && n && i ? t.ref = mr(n, i) : t[e] = i === void 0 ? n : i;
		}
	}
	return t;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocus.mjs
function vr(e) {
	let { isDisabled: t, onFocus: n, onBlur: r, onFocusChange: i } = e, a = (0, x.useCallback)((e) => {
		if (z(e) === e.currentTarget) return r && r(e), i && i(!1), !0;
	}, [r, i]), o = Yt(a), s = (0, x.useCallback)((e) => {
		let t = z(e), r = L(t), a = r ? Ft(r) : Ft();
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
function yr(e) {
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
var br = /* @__PURE__ */ new Set([
	"shift",
	"alt",
	"control",
	"meta",
	"mod"
]), xr = [
	"Alt",
	"Control",
	"Meta",
	"Shift"
];
function Sr(e) {
	let t = /* @__PURE__ */ new Set();
	return e.alt && t.add("Alt"), e.shift && t.add("Shift"), e.ctrl && t.add("Control"), e.meta && t.add("Meta"), e.mod && t.add(tn() ? "Meta" : "Control"), t;
}
function Cr(e) {
	let t = /* @__PURE__ */ new Set();
	return e.altKey && t.add("Alt"), e.ctrlKey && t.add("Control"), e.metaKey && t.add("Meta"), e.shiftKey && t.add("Shift"), t;
}
function wr(e) {
	return xr.filter((t) => e.has(t));
}
function Tr(e) {
	let t = e.split("+").reduce((e, t) => {
		let n = t.toLowerCase();
		return br.has(n) ? n === "shift" ? e.shift = !0 : n === "alt" ? e.alt = !0 : n === "control" ? e.ctrl = !0 : n === "meta" ? e.meta = !0 : n === "mod" && (e.mod = !0) : e.key = t, e;
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
function Er(e) {
	return e.toLowerCase();
}
var Dr = {
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
function Or(e) {
	let t = Er(e);
	return Dr[t] ?? t;
}
function kr(e) {
	let t = wr(Sr(e)), n = Or(e.key);
	return t.length > 0 ? `${t.join("+")}+${n}` : n;
}
function Ar(e) {
	let t = wr(Cr(e)), n = Er(e.key);
	return (t.length > 0 ? `${t.join("+")}+` : "") + n;
}
function jr(e) {
	let t = /* @__PURE__ */ new Map();
	for (let [n, r] of Object.entries(e)) {
		let e = Tr(n);
		t.set(kr(e), r);
	}
	return (e) => {
		let n = Ar(e), r = t.get(n), i = r?.(e);
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
function Mr(e) {
	let { shortcuts: t, allowRepeats: n = !1, allowComposing: r = !1 } = e, i, a;
	if (t) {
		let o = jr(t), s = yr((e) => {
			if (!R(e.currentTarget, z(e))) {
				e.continuePropagation();
				return;
			}
			if (e.nativeEvent?.repeat && !n || e.nativeEvent?.isComposing && !r) {
				e.continuePropagation();
				return;
			}
			o(e);
		}), c = yr((e) => {
			if (!R(e.currentTarget, z(e))) {
				e.continuePropagation();
				return;
			}
			if (e.nativeEvent?.repeat && !n || e.nativeEvent?.isComposing && !r) {
				e.continuePropagation();
				return;
			}
			e.continuePropagation();
		});
		i = e.onKeyDown ? ar(e.onKeyDown, s) : s, a = e.onKeyUp ? ar(e.onKeyUp, c) : c;
	} else i = yr(e.onKeyDown), a = yr(e.onKeyUp);
	return { keyboardProps: e.isDisabled ? {} : {
		onKeyDown: i,
		onKeyUp: a
	} };
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useObjectRef.mjs
function Nr(e) {
	let t = (0, x.useRef)(null), n = (0, x.useRef)(void 0), r = (0, x.useCallback)((t) => {
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
	return (0, x.useMemo)(() => ({
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
function Pr(e, t) {
	V(() => {
		if (e && e.ref && t) return e.ref.current = t.current, () => {
			e.ref && (e.ref.current = null);
		};
	});
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useFocusable.mjs
var Fr = /*#__PURE__*/ x.createContext(null);
function Ir(e) {
	let t = (0, x.useContext)(Fr) || {};
	Pr(t, e);
	let { ref: n, ...r } = t;
	return r;
}
function Lr(e, t) {
	let { focusProps: n } = vr(e), { keyboardProps: r } = Mr(e), i = H(n, r), a = Ir(t), o = e.isDisabled ? {} : a, s = (0, x.useRef)(e.autoFocus);
	(0, x.useEffect)(() => {
		s.current && t.current && ir(t.current), s.current = !1;
	}, [t]);
	let c = e.excludeFromTabOrder ? -1 : 0;
	return e.isDisabled && (c = void 0), { focusableProps: H({
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
var Rr = /*#__PURE__*/ (0, x.createContext)(!1);
function zr(e) {
	if ((0, x.useContext)(Rr)) return /*#__PURE__*/ x.createElement(x.Fragment, null, e.children);
	let t = /*#__PURE__*/ x.createElement(Rr.Provider, { value: !0 }, e.children);
	return /*#__PURE__*/ x.createElement("template", null, t);
}
function Br(e) {
	let t = (t, n) => (0, x.useContext)(Rr) ? null : e(t, n);
	return t.displayName = e.displayName || e.name, (0, x.forwardRef)(t);
}
function Vr() {
	return (0, x.useContext)(Rr);
}
//#endregion
//#region node_modules/react-dom/cjs/react-dom.production.js
var Hr = /* @__PURE__ */ m(((e) => {
	var t = v();
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
})), Ur = /* @__PURE__ */ m(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = Hr();
})), Wr = /* @__PURE__ */ m(((e) => {
	var t = v();
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
})), Gr = /* @__PURE__ */ m(((e, t) => {
	t.exports = Wr();
})), Kr = /* @__PURE__ */ g(Ur(), 1), qr = Gr(), Jr = /*#__PURE__*/ (0, x.createContext)(!1), Yr = /*#__PURE__*/ (0, x.createContext)(null);
function Xr(e) {
	if ((0, x.useContext)(Yr)) return e.content;
	let { collection: t, document: n } = ei(e.createCollection);
	return /*#__PURE__*/ x.createElement(x.Fragment, null, /*#__PURE__*/ x.createElement(zr, null, /*#__PURE__*/ x.createElement(Yr.Provider, { value: n }, e.content)), /*#__PURE__*/ x.createElement(Zr, {
		render: e.children,
		collection: t
	}));
}
function Zr({ collection: e, render: t }) {
	return t(e);
}
function Qr(e, t, n) {
	let r = An(), i = (0, x.useRef)(r);
	i.current = r;
	let a = (0, x.useCallback)(() => i.current ? n() : t(), [t, n]);
	return (0, qr.useSyncExternalStore)(e, a);
}
var $r = typeof x.useSyncExternalStore == "function" ? x.useSyncExternalStore : Qr;
function ei(e) {
	let [t] = (0, x.useState)(() => new vt(e?.() || new mt()));
	return {
		collection: $r((0, x.useCallback)((e) => t.subscribe(e), [t]), (0, x.useCallback)(() => {
			let e = t.getCollection();
			return t.isSSR && t.resetAfterSSR(), e;
		}, [t]), (0, x.useCallback)(() => (t.isSSR = !0, t.getCollection()), [t])),
		document: t
	};
}
var ti = /*#__PURE__*/ (0, x.createContext)(null);
function ni(e) {
	return class extends ut {
		static {
			this.type = e;
		}
	};
}
function ri(e, t, n, r, i, a) {
	typeof e == "string" && (e = ni(e));
	let o = (0, x.useCallback)((i) => {
		i?.setProps(t, n, e, r, a);
	}, [
		t,
		n,
		r,
		a,
		e
	]), s = (0, x.useContext)(ti);
	if (s) {
		let o = s.ownerDocument.nodesByProps.get(t);
		return o || (o = s.ownerDocument.createElement(e.type), o.setProps(t, n, e, r, a), s.appendChild(o), s.ownerDocument.updateCollection(), s.ownerDocument.nodesByProps.set(t, o)), i ? /*#__PURE__*/ x.createElement(ti.Provider, { value: o }, i) : null;
	}
	return /*#__PURE__*/ x.createElement(e.type, { ref: o }, i);
}
function ii(e, t) {
	let n = ({ node: e }) => t(e.props, e.props.ref, e), r = (0, x.forwardRef)((r, i) => {
		let a = (0, x.useContext)(Fr);
		if (!(0, x.useContext)(Jr)) {
			if (t.length >= 3) throw Error(t.name + " cannot be rendered outside a collection.");
			return t(r, i);
		}
		return ri(e, r, i, "children" in r ? r.children : null, null, (e) => /*#__PURE__*/ x.createElement(Fr.Provider, { value: a }, /*#__PURE__*/ x.createElement(n, { node: e })));
	});
	return r.displayName = t.name, r;
}
function ai(e) {
	return yt({
		...e,
		addIdAndValue: !0
	});
}
var oi = /*#__PURE__*/ (0, x.createContext)(null);
function si(e) {
	let t = (0, x.useContext)(oi), n = (t?.dependencies || []).concat(e.dependencies), r = e.idScope ?? t?.idScope, i = ai({
		...e,
		idScope: r,
		dependencies: n
	});
	return (0, x.useContext)(Yr) && (i = /*#__PURE__*/ x.createElement(ci, null, i)), t = (0, x.useMemo)(() => ({
		dependencies: n,
		idScope: r
	}), [r, ...n]), /*#__PURE__*/ x.createElement(oi.Provider, { value: t }, i);
}
function ci({ children: e }) {
	let t = (0, x.useContext)(Yr), n = (0, x.useMemo)(() => /*#__PURE__*/ x.createElement(Yr.Provider, { value: null }, /*#__PURE__*/ x.createElement(Jr.Provider, { value: !0 }, e)), [e]);
	return An() ? /*#__PURE__*/ x.createElement(ti.Provider, { value: t }, n) : /*#__PURE__*/ (0, Kr.createPortal)(n, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/constants.mjs
var li = "react-aria-clear-focus", ui = "react-aria-focus";
//#endregion
//#region node_modules/react-aria/dist/private/focus/virtualFocus.mjs
function di(e) {
	let t = mi(L(e));
	t !== e && (t && fi(t, e), e && pi(e, t));
}
function fi(e, t) {
	e.dispatchEvent(new FocusEvent("blur", { relatedTarget: t })), e.dispatchEvent(new FocusEvent("focusout", {
		bubbles: !0,
		relatedTarget: t
	}));
}
function pi(e, t) {
	e.dispatchEvent(new FocusEvent("focus", { relatedTarget: t })), e.dispatchEvent(new FocusEvent("focusin", {
		bubbles: !0,
		relatedTarget: t
	}));
}
function mi(e) {
	let t = Ft(e), n = t?.getAttribute("aria-activedescendant");
	return n && e.getElementById(n) || t;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/keyboard.mjs
function hi(e) {
	return tn() ? e.metaKey : e.ctrlKey;
}
var gi = /* @__PURE__ */ new Set([
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
function _i(e) {
	return e instanceof HTMLInputElement && !gi.has(e.type) || e instanceof HTMLTextAreaElement || e instanceof HTMLElement && e.isContentEditable;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useEffectEvent.mjs
var vi = x.useInsertionEffect ?? V;
function yi(e) {
	let t = (0, x.useRef)(null);
	return vi(() => {
		t.current = e;
	}, [e]), (0, x.useCallback)((...e) => {
		let n = t.current;
		return n?.(...e);
	}, []);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useEvent.mjs
function bi(e, t, n, r) {
	let i = yi(n), a = n == null;
	(0, x.useEffect)(() => {
		if (!(a || e.current == null)) return jt(e.current, t, i, r);
	}, [
		e,
		t,
		r,
		a
	]);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useLabels.mjs
function xi(e, t) {
	let { id: n, "aria-label": r, "aria-labelledby": i } = e;
	return n = dr(n), i && r ? i = [.../* @__PURE__ */ new Set([n, ...i.trim().split(/\s+/)])].join(" ") : i &&= i.trim().split(/\s+/).join(" "), !r && !i && t && (r = t), {
		id: n,
		"aria-label": r,
		"aria-labelledby": i
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/utils.mjs
var Si = /* @__PURE__ */ new Set([
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
]), Ci = /* @__PURE__ */ new Set([
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
function wi(e) {
	if (Intl.Locale) {
		let t = new Intl.Locale(e).maximize(), n = typeof t.getTextInfo == "function" ? t.getTextInfo() : t.textInfo;
		if (n) return n.direction === "rtl";
		if (t.script) return Si.has(t.script);
	}
	let t = e.split("-")[0];
	return Ci.has(t);
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/useDefaultLocale.mjs
var Ti = Symbol.for("react-aria.i18n.locale");
function Ei() {
	let e = typeof window < "u" && window[Ti] || typeof navigator < "u" && (navigator.language || navigator.userLanguage) || "en-US";
	try {
		Intl.DateTimeFormat.supportedLocalesOf([e]);
	} catch {
		e = "en-US";
	}
	return {
		locale: e,
		direction: wi(e) ? "rtl" : "ltr"
	};
}
var Di = Ei(), Oi = /* @__PURE__ */ new Set();
function ki() {
	Di = Ei();
	for (let e of Oi) e(Di);
}
function Ai() {
	let e = An(), [t, n] = (0, x.useState)(Di);
	return (0, x.useEffect)(() => (Oi.size === 0 && window.addEventListener("languagechange", ki), Oi.add(n), () => {
		Oi.delete(n), Oi.size === 0 && window.removeEventListener("languagechange", ki);
	}), []), e ? {
		locale: typeof window < "u" && window[Ti] || "en-US",
		direction: "ltr"
	} : t;
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/I18nProvider.mjs
var ji = /*#__PURE__*/ x.createContext(null);
function Mi() {
	let e = Ai();
	return (0, x.useContext)(ji) || e;
}
//#endregion
//#region node_modules/@internationalized/string/dist/private/LocalizedStringDictionary.mjs
var Ni = Symbol.for("react-aria.i18n.locale"), Pi = Symbol.for("react-aria.i18n.strings"), Fi = void 0, Ii = class e {
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
		return t || (t = Li(e, this.strings, this.defaultLocale), this.strings[e] = t), t;
	}
	static getGlobalDictionaryForPackage(t) {
		if (typeof window > "u") return null;
		let n = window[Ni];
		if (Fi === void 0) {
			let t = window[Pi];
			if (!t) return null;
			Fi = {};
			for (let r in t) Fi[r] = new e({ [n]: t[r] }, n);
		}
		let r = Fi?.[t];
		if (!r) throw Error(`Strings for package "${t}" were not included by LocalizedStringProvider. Please add it to the list passed to createLocalizedStringDictionary.`);
		return r;
	}
};
function Li(e, t, n = "en-US") {
	if (t[e]) return t[e];
	let r = Ri(e), i = zi(e);
	if (i && t[`${r}-${i}`]) return t[`${r}-${i}`];
	if (t[r]) return t[r];
	for (let e in t) if (e.startsWith(r + "-")) return t[e];
	return t[n];
}
function Ri(e) {
	return Intl.Locale ? new Intl.Locale(e).language : e.split("-")[0];
}
function zi(e) {
	if (Intl.Locale) return new Intl.Locale(e).script;
}
//#endregion
//#region node_modules/@internationalized/string/dist/private/LocalizedStringFormatter.mjs
var Bi = /* @__PURE__ */ new Map(), Vi = /* @__PURE__ */ new Map(), Hi = class {
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
		let i = this.locale + ":" + n, a = Bi.get(i);
		return a || (a = new Intl.PluralRules(this.locale, { type: n }), Bi.set(i, a)), r = t[a.select(e)] || t.other, typeof r == "function" ? r() : r;
	}
	number(e) {
		let t = Vi.get(this.locale);
		return t || (t = new Intl.NumberFormat(this.locale), Vi.set(this.locale, t)), t.format(e);
	}
	select(e, t) {
		let n = e[t] || e.other;
		return typeof n == "function" ? n() : n;
	}
}, Ui = /* @__PURE__ */ new WeakMap();
function Wi(e) {
	let t = Ui.get(e);
	return t || (t = new Ii(e), Ui.set(e, t)), t;
}
function Gi(e, t) {
	return t && Ii.getGlobalDictionaryForPackage(t) || Wi(e);
}
function Ki(e, t) {
	let { locale: n } = Mi(), r = Gi(e, t);
	return (0, x.useMemo)(() => new Hi(n, r), [n, r]);
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/filterDOMProps.mjs
var qi = /* @__PURE__ */ new Set(["id"]), Ji = /* @__PURE__ */ new Set([
	"aria-label",
	"aria-labelledby",
	"aria-describedby",
	"aria-details"
]), Yi = /* @__PURE__ */ new Set([
	"href",
	"hrefLang",
	"target",
	"rel",
	"download",
	"ping",
	"referrerPolicy"
]), Xi = /* @__PURE__ */ new Set([
	"dir",
	"lang",
	"hidden",
	"inert",
	"translate"
]), Zi = /* @__PURE__ */ new Set(/* @__PURE__ */ "onClick.onAuxClick.onContextMenu.onDoubleClick.onMouseDown.onMouseEnter.onMouseLeave.onMouseMove.onMouseOut.onMouseOver.onMouseUp.onTouchCancel.onTouchEnd.onTouchMove.onTouchStart.onPointerDown.onPointerMove.onPointerUp.onPointerCancel.onPointerEnter.onPointerLeave.onPointerOver.onPointerOut.onGotPointerCapture.onLostPointerCapture.onScroll.onWheel.onAnimationStart.onAnimationEnd.onAnimationIteration.onTransitionCancel.onTransitionEnd.onTransitionRun.onTransitionStart".split(".")), Qi = /^(data-.*)$/;
function U(e, t = {}) {
	let { labelable: n, isLink: r, global: i, events: a = i, propNames: o } = t, s = {};
	for (let t in e) Object.prototype.hasOwnProperty.call(e, t) && (qi.has(t) || n && Ji.has(t) || r && Yi.has(t) || i && Xi.has(t) || a && (Zi.has(t) || t.endsWith("Capture") && Zi.has(t.slice(0, -7))) || o?.has(t) || Qi.test(t)) && (s[t] = e[t]);
	return s;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/textSelection.mjs
var $i = "default", W = "", ea = /* @__PURE__ */ new WeakMap();
function ta(e) {
	if (an() && sn()) {
		if ($i === "default") {
			let t = L(e);
			W = t.documentElement.style.webkitUserSelect, t.documentElement.style.webkitUserSelect = "none";
		}
		$i = "disabled";
	} else if (e instanceof HTMLElement || e instanceof SVGElement) {
		let t = "userSelect" in e.style ? "userSelect" : "webkitUserSelect";
		ea.set(e, e.style[t]), e.style[t] = "none";
	}
}
function na(e) {
	if (an() && sn()) {
		if ($i !== "disabled") return;
		$i = "restoring", setTimeout(() => {
			rr(() => {
				if ($i === "restoring") {
					let t = L(e);
					t.documentElement.style.webkitUserSelect === "none" && (t.documentElement.style.webkitUserSelect = W || ""), W = "", $i = "default";
				}
			});
		}, 300);
	} else if ((e instanceof HTMLElement || e instanceof SVGElement) && e && ea.has(e)) {
		let t = ea.get(e), n = "userSelect" in e.style ? "userSelect" : "webkitUserSelect";
		e.style[n] === "none" && (e.style[n] = t), e.getAttribute("style") === "" && e.removeAttribute("style"), ea.delete(e);
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getMetaValue.mjs
function ra(e, t) {
	let n = Et(t), r = L(t);
	if (r == null || n == null) return;
	let i, a = `meta[name="${CSS.escape(e)}"], meta[property="${CSS.escape(e)}"]`, o = r.querySelector(a);
	return o && o instanceof n.HTMLMetaElement && (e === "csp-nonce" && o.nonce && (i ??= o.nonce || void 0), o.content && (i ??= o.content || void 0)), e === "csp-nonce" && (i ??= n.__webpack_nonce__ || globalThis.__webpack_nonce__ || void 0), i;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getNonce.mjs
var ia = /* @__PURE__ */ new WeakMap();
function aa(e) {
	let t = L(e), n = ia.get(t);
	return n ??= ra("csp-nonce", t), n !== void 0 && ia.set(t, n), n;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/context.mjs
var oa = x.createContext({ register: () => {} });
oa.displayName = "PressResponderContext";
//#endregion
//#region node_modules/react-aria/dist/private/utils/useGlobalListeners.mjs
function sa() {
	let e = (0, x.useRef)(/* @__PURE__ */ new Map()), t = (0, x.useCallback)((t, n, r, i) => {
		let a = i?.once ? (...t) => {
			e.current.delete(r), r(...t);
		} : r;
		e.current.set(r, {
			type: n,
			eventTarget: t,
			fn: a,
			options: i
		}), t.addEventListener(n, a, i);
	}, []), n = (0, x.useCallback)((t, n, r, i) => {
		let a = e.current.get(r)?.fn || r;
		t.removeEventListener(n, a, i), e.current.delete(r);
	}, []), r = (0, x.useCallback)(() => {
		e.current.forEach((e, t) => {
			n(e.eventTarget, e.type, t, e.options);
		});
	}, [n]);
	return (0, x.useEffect)(() => r, [r]), {
		addGlobalListener: t,
		removeGlobalListener: n,
		removeAllGlobalListeners: r
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/usePress.mjs
function ca(e) {
	let t = (0, x.useContext)(oa);
	if (t) {
		let { register: n, ref: r, ...i } = t;
		e = H(i, e), n();
	}
	return Pr(t, e.ref), e;
}
var la = class {
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
}, ua = Symbol("linkClicked"), da = "react-aria-pressable-style", fa = "data-react-aria-pressable";
function pa(e) {
	let { onPress: t, onPressChange: n, onPressStart: r, onPressEnd: i, onPressUp: a, onClick: o, isDisabled: s, isPressed: c, preventFocusOnPress: l, shouldCancelOnPointerExit: u, allowTextSelectionOnPress: d, ref: f, ...p } = ca(e), [m, h] = (0, x.useState)(!1), g = (0, x.useRef)({
		isPressed: !1,
		ignoreEmulatedMouseEvents: !1,
		didFirePressStart: !1,
		isTriggeringEvent: !1,
		activePointerId: null,
		target: null,
		isOverTarget: !1,
		pointerType: null,
		disposables: []
	}), { addGlobalListener: _, removeAllGlobalListeners: v } = sa(), y = (0, x.useCallback)((e, t) => {
		let i = g.current;
		if (s || i.didFirePressStart) return !1;
		let a = !0;
		if (i.isTriggeringEvent = !0, r) {
			let n = new la("pressstart", t, e);
			r(n), a = n.shouldStopPropagation;
		}
		return n && n(!0), i.isTriggeringEvent = !1, i.didFirePressStart = !0, h(!0), a;
	}, [
		s,
		r,
		n
	]), b = (0, x.useCallback)((e, r, a = !0) => {
		let o = g.current;
		if (!o.didFirePressStart) return !1;
		o.didFirePressStart = !1, o.isTriggeringEvent = !0;
		let c = !0;
		if (i) {
			let t = new la("pressend", r, e);
			i(t), c = t.shouldStopPropagation;
		}
		if (n && n(!1), h(!1), t && a && !s) {
			let n = new la("press", r, e);
			t(n), c &&= n.shouldStopPropagation;
		}
		return o.isTriggeringEvent = !1, c;
	}, [
		s,
		i,
		n,
		t
	]), S = yi(b), C = yi((0, x.useCallback)((e, t) => {
		let n = g.current;
		if (s) return !1;
		if (a) {
			n.isTriggeringEvent = !0;
			let r = new la("pressup", t, e);
			return a(r), n.isTriggeringEvent = !1, r.shouldStopPropagation;
		}
		return !0;
	}, [s, a])), w = (0, x.useCallback)((e) => {
		let t = g.current;
		if (t.isPressed && t.target) {
			t.didFirePressStart && t.pointerType != null && b(ga(t.target, e), t.pointerType, !1), t.isPressed = !1, t.isOverTarget = !1, t.activePointerId = null, t.pointerType = null, v(), d || na(t.target);
			for (let e of t.disposables) e();
			t.disposables = [];
		}
	}, [
		d,
		v,
		b
	]), T = yi(w);
	(0, x.useEffect)(() => {
		s && g.current.isPressed && T({
			currentTarget: g.current.target,
			shiftKey: !1,
			ctrlKey: !1,
			metaKey: !1,
			altKey: !1
		});
	}, [s]);
	let E = (0, x.useCallback)((e) => {
		u && w(e);
	}, [u, w]), D = (0, x.useCallback)((e) => {
		s || o?.(e);
	}, [s, o]), O = (0, x.useCallback)((e, t) => {
		if (!s && o) {
			let n = new MouseEvent("click", e);
			Jt(n, t), o(qt(n));
		}
	}, [s, o]), k = (0, x.useMemo)(() => {
		let e = g.current, t = {
			onKeyDown(t) {
				if (ha(t.nativeEvent, t.currentTarget) && R(t.currentTarget, z(t))) {
					va(z(t), t.key) && t.preventDefault();
					let r = !0;
					!e.isPressed && !t.repeat && (e.target = t.currentTarget, e.isPressed = !0, e.pointerType = "keyboard", r = y(t, "keyboard"));
					let i = t.currentTarget;
					_(L(t.currentTarget), "keyup", ar((t) => {
						ha(t, i) && !t.repeat && R(i, z(t)) && e.target && C(ga(e.target, t), "keyboard");
					}, n), !0), r && t.stopPropagation(), t.metaKey && tn() && e.metaKeyEvents?.set(t.key, t.nativeEvent);
				} else t.key === "Meta" && (e.metaKeyEvents = /* @__PURE__ */ new Map());
			},
			onClick(t) {
				if (!(t && !R(t.currentTarget, z(t))) && t && t.button === 0 && !e.isTriggeringEvent && !hn.isOpening) {
					let n = !0;
					if (s && t.preventDefault(), !e.ignoreEmulatedMouseEvents && !e.isPressed && (e.pointerType === "virtual" || dn(t.nativeEvent))) {
						let e = y(t, "virtual"), r = C(t, "virtual"), i = S(t, "virtual");
						D(t), n = e && r && i;
					} else if (e.isPressed && e.pointerType !== "keyboard") {
						let r = e.pointerType || t.nativeEvent.pointerType || "virtual", i = C(ga(t.currentTarget, t), r), a = S(ga(t.currentTarget, t), r, !0);
						n = i && a, e.isOverTarget = !1, D(t), T(t);
					}
					e.ignoreEmulatedMouseEvents = !1, n && t.stopPropagation();
				}
			}
		}, n = (t) => {
			if (e.isPressed && e.target && ha(t, e.target)) {
				va(z(t), t.key) && t.preventDefault();
				let n = z(t), r = R(e.target, n);
				S(ga(e.target, t), "keyboard", r), r && O(t, e.target), v(), t.key !== "Enter" && ma(e.target) && R(e.target, n) && !t[ua] && (t[ua] = !0, hn(e.target, t, !1)), e.isPressed = !1, e.metaKeyEvents?.delete(t.key);
			} else if (t.key === "Meta" && e.metaKeyEvents?.size) {
				let t = e.metaKeyEvents;
				e.metaKeyEvents = void 0;
				for (let n of t.values()) e.target?.dispatchEvent(new KeyboardEvent("keyup", n));
			}
		};
		if (typeof PointerEvent < "u") {
			t.onPointerDown = (t) => {
				if (t.button !== 0 || !R(t.currentTarget, z(t))) return;
				if (fn(t.nativeEvent)) {
					e.pointerType = "virtual";
					return;
				}
				e.pointerType = t.pointerType;
				let i = !0;
				if (!e.isPressed) {
					e.isPressed = !0, e.isOverTarget = !0, e.activePointerId = t.pointerId, e.target = t.currentTarget, d || ta(e.target), i = y(t, e.pointerType);
					let a = z(t);
					"releasePointerCapture" in a && ("hasPointerCapture" in a ? a.hasPointerCapture(t.pointerId) && a.releasePointerCapture(t.pointerId) : a.releasePointerCapture(t.pointerId)), _(L(t.currentTarget), "pointerup", n, !1), _(L(t.currentTarget), "pointercancel", r, !1);
				}
				i && t.stopPropagation();
			}, t.onMouseDown = (t) => {
				if (R(t.currentTarget, z(t)) && t.button === 0) {
					if (l) {
						let n = Zt(t.target);
						n && e.disposables.push(n);
					}
					t.stopPropagation();
				}
			}, t.onPointerUp = (t) => {
				!R(t.currentTarget, z(t)) || e.pointerType === "virtual" || t.button === 0 && !e.isPressed && C(t, e.pointerType || t.pointerType);
			}, t.onPointerEnter = (t) => {
				t.pointerId === e.activePointerId && e.target && !e.isOverTarget && e.pointerType != null && (e.isOverTarget = !0, y(ga(e.target, t), e.pointerType));
			}, t.onPointerLeave = (t) => {
				t.pointerId === e.activePointerId && e.target && e.isOverTarget && e.pointerType != null && (e.isOverTarget = !1, S(ga(e.target, t), e.pointerType, !1), E(t));
			};
			let n = (t) => {
				if (t.pointerId === e.activePointerId && e.isPressed && t.button === 0 && e.target) {
					if (R(e.target, z(t)) && e.pointerType != null) {
						let n = !1, r = setTimeout(() => {
							e.isPressed && e.target instanceof HTMLElement && (n ? T(t) : (xt(e.target), e.target.click()));
						}, 80);
						_(t.currentTarget, "click", () => n = !0, !0), e.disposables.push(() => clearTimeout(r));
					} else T(t);
					e.isOverTarget = !1;
				}
			}, r = (e) => {
				T(e);
			};
			t.onDragStart = (e) => {
				R(e.currentTarget, z(e)) && T(e);
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
	return (0, x.useEffect)(() => {
		if (!f) return;
		let e = L(f.current);
		if (!e || !e.head || e.getElementById(da)) return;
		let t = e.createElement("style");
		t.id = da;
		let n = aa(e);
		n && (t.nonce = n), t.textContent = `
@layer {
  [${fa}] {
    touch-action: pan-x pan-y pinch-zoom;
  }
}
    `.trim(), e.head.prepend(t);
	}, [f]), (0, x.useEffect)(() => {
		let e = g.current;
		return () => {
			d || na(e.target ?? void 0);
			for (let t of e.disposables) t();
			e.disposables = [];
		};
	}, [d]), {
		isPressed: c || m,
		pressProps: H(p, k, { [fa]: !0 })
	};
}
function ma(e) {
	return e.tagName === "A" && e.hasAttribute("href");
}
function ha(e, t) {
	let { key: n, code: r } = e, i = t, a = i.getAttribute("role");
	return (n === "Enter" || n === " " || n === "Spacebar" || r === "Space") && !(i instanceof Et(i).HTMLInputElement && !ba(i, n) || i instanceof Et(i).HTMLTextAreaElement || i.isContentEditable) && !((a === "link" || !a && ma(i)) && n !== "Enter");
}
function ga(e, t) {
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
function _a(e) {
	return e instanceof HTMLInputElement ? !1 : e instanceof HTMLButtonElement ? e.type !== "submit" && e.type !== "reset" : !ma(e);
}
function va(e, t) {
	return tn() && t === "Enter" ? !1 : e instanceof HTMLInputElement ? t === "Enter" && (e.type === "checkbox" || e.type === "radio") ? !1 : !ba(e, t) : _a(e);
}
var ya = /* @__PURE__ */ new Set([
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
function ba(e, t) {
	return e.type === "checkbox" || e.type === "radio" ? t === " " : ya.has(e.type);
}
//#endregion
//#region node_modules/react-aria/dist/private/button/useButton.mjs
function xa(e, t) {
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
	let { pressProps: _, isPressed: v } = pa({
		onPressStart: a,
		onPressEnd: o,
		onPressChange: c,
		onPress: i,
		onPressUp: s,
		onClick: d,
		isDisabled: r,
		preventFocusOnPress: l,
		ref: t
	}), { focusableProps: y } = Lr(e, t);
	u && (y.tabIndex = r ? -1 : y.tabIndex);
	let b = H(y, _, U(e, { labelable: !0 }));
	return {
		isPressed: v,
		buttonProps: H(g, b, {
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
var Sa = class {
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
		if (!R(this.root, e)) throw Error("Cannot set currentNode to a node that is not contained by the root node.");
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
		return R(e, t) ? (t && (this.currentNode = t), t) : (this.currentNode = e, null);
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
function Ca(e, t, n, r) {
	return Pt() ? new Sa(e, t, n, r) : e.createTreeWalker(t, n, r);
}
//#endregion
//#region node_modules/react-aria/dist/private/focus/FocusScope.mjs
var wa = /*#__PURE__*/ x.createContext(null), Ta = "react-aria-focus-scope-restore", G = null;
function Ea(e) {
	let { children: t, contain: n, restoreFocus: r, autoFocus: i } = e, a = (0, x.useRef)(null), o = (0, x.useRef)(null), s = (0, x.useRef)([]), { parentNode: c } = (0, x.useContext)(wa) || {}, l = (0, x.useMemo)(() => new Ja({ scopeRef: s }), [s]);
	V(() => {
		let e = c || Ya.root;
		if (Ya.getTreeNode(e.scopeRef) && G && !La(G, e.scopeRef)) {
			let t = Ya.getTreeNode(G);
			t && (e = t);
		}
		e.addChild(l), Ya.addNode(l);
	}, [l, c]), V(() => {
		let e = Ya.getTreeNode(s);
		e && (e.contain = !!n);
	}, [n]), V(() => {
		let e = a.current?.nextSibling, t = [], n = (e) => e.stopPropagation();
		for (; e && e !== o.current;) t.push(e), e.addEventListener(Ta, n), e = e.nextSibling;
		return s.current = t, () => {
			for (let e of t) e.removeEventListener(Ta, n);
		};
	}, [t]), Ha(s, r, n), Ma(s, n), Wa(s, r, n), Va(s, i), (0, x.useEffect)(() => {
		let e = Ft(L(s.current ? s.current[0] : void 0)), t = null;
		if (Pa(e, s.current)) {
			for (let n of Ya.traverse()) n.scopeRef && Pa(e, n.scopeRef.current) && (t = n);
			t === Ya.getTreeNode(s) && (G = t.scopeRef);
		}
	}, [s]), V(() => () => {
		let e = Ya.getTreeNode(s)?.parent?.scopeRef ?? null;
		(s === G || La(s, G)) && (!e || Ya.getTreeNode(e)) && (G = e), Ya.removeTreeNode(s);
	}, [s]);
	let u = (0, x.useMemo)(() => Da(s), []), d = (0, x.useMemo)(() => ({
		focusManager: u,
		parentNode: l
	}), [l, u]);
	return /*#__PURE__*/ x.createElement(wa.Provider, { value: d }, /*#__PURE__*/ x.createElement("span", {
		"data-focus-scope-start": !0,
		hidden: !0,
		ref: a
	}), t, /*#__PURE__*/ x.createElement("span", {
		"data-focus-scope-end": !0,
		hidden: !0,
		ref: o
	}));
}
function Da(e) {
	return {
		focusNext(t = {}) {
			let n = e.current, { from: r, tabbable: i, wrap: a, accept: o } = t, s = r || Ft(L(n[0] ?? void 0)), c = n[0].previousElementSibling, l = Ka(Oa(n), {
				tabbable: i,
				accept: o
			}, n);
			l.currentNode = Pa(s, n) ? s : c;
			let u = l.nextNode();
			return !u && a && (l.currentNode = c, u = l.nextNode()), u && Ra(u, !0), u;
		},
		focusPrevious(t = {}) {
			let n = e.current, { from: r, tabbable: i, wrap: a, accept: o } = t, s = r || Ft(L(n[0] ?? void 0)), c = n[n.length - 1].nextElementSibling, l = Ka(Oa(n), {
				tabbable: i,
				accept: o
			}, n);
			l.currentNode = Pa(s, n) ? s : c;
			let u = l.previousNode();
			return !u && a && (l.currentNode = c, u = l.previousNode()), u && Ra(u, !0), u;
		},
		focusFirst(t = {}) {
			let n = e.current, { tabbable: r, accept: i } = t, a = Ka(Oa(n), {
				tabbable: r,
				accept: i
			}, n);
			a.currentNode = n[0].previousElementSibling;
			let o = a.nextNode();
			return o && Ra(o, !0), o;
		},
		focusLast(t = {}) {
			let n = e.current, { tabbable: r, accept: i } = t, a = Ka(Oa(n), {
				tabbable: r,
				accept: i
			}, n);
			a.currentNode = n[n.length - 1].nextElementSibling;
			let o = a.previousNode();
			return o && Ra(o, !0), o;
		}
	};
}
function Oa(e) {
	return e[0].parentElement;
}
function ka(e) {
	let t = Ya.getTreeNode(G);
	for (; t && t.scopeRef !== e;) {
		if (t.contain) return !1;
		t = t.parent;
	}
	return !0;
}
function Aa(e) {
	if (!e.form) return Array.from(L(e).querySelectorAll(`input[type="radio"][name="${CSS.escape(e.name)}"]`)).filter((e) => !e.form);
	let t = e.form.elements.namedItem(e.name), n = Et(e);
	return t instanceof n.RadioNodeList ? Array.from(t).filter((e) => e instanceof n.HTMLInputElement) : t instanceof n.HTMLInputElement ? [t] : [];
}
function ja(e) {
	if (e.checked) return !0;
	let t = Aa(e);
	return t.length > 0 && !t.some((e) => e.checked);
}
function Ma(e, t) {
	let n = (0, x.useRef)(void 0), r = (0, x.useRef)(void 0);
	V(() => {
		let i = e.current;
		if (!t) {
			r.current &&= (cancelAnimationFrame(r.current), void 0);
			return;
		}
		let a = L(i ? i[0] : void 0), o = (t) => {
			if (t.key !== "Tab" || t.altKey || t.ctrlKey || t.metaKey || !ka(e) || t.isComposing) return;
			let n = Ft(a), r = e.current;
			if (!r || !Pa(n, r)) return;
			let i = Ka(Oa(r), { tabbable: !0 }, r);
			if (!n) return;
			i.currentNode = n;
			let o = t.shiftKey ? i.previousNode() : i.nextNode();
			o ||= (i.currentNode = t.shiftKey ? r[r.length - 1].nextElementSibling : r[0].previousElementSibling, t.shiftKey ? i.previousNode() : i.nextNode()), t.preventDefault(), o && (Ra(o, !0), o instanceof Et(o).HTMLInputElement && o.select());
		}, s = (t) => {
			(!G || La(G, e)) && Pa(z(t), e.current) ? (G = e, n.current = z(t)) : ka(e) && !Fa(z(t), e) ? n.current ? Ra(n.current) : G && G.current && Ba(G.current) : ka(e) && (n.current = z(t));
		}, c = (t) => {
			r.current && cancelAnimationFrame(r.current), r.current = requestAnimationFrame(() => {
				let r = Jn(), i = (r === "virtual" || r === null) && ln() && cn(), o = Ft(a);
				if (!i && o && ka(e) && !Fa(o, e)) {
					G = e;
					let r = z(t);
					r && r.isConnected ? (n.current = r, Ra(n.current)) : G.current && Ba(G.current);
				}
			});
		};
		return a.addEventListener("keydown", o, !1), a.addEventListener("focusin", s, !1), i?.forEach((e) => e.addEventListener("focusin", s, !1)), i?.forEach((e) => e.addEventListener("focusout", c, !1)), () => {
			a.removeEventListener("keydown", o, !1), a.removeEventListener("focusin", s, !1), i?.forEach((e) => e.removeEventListener("focusin", s, !1)), i?.forEach((e) => e.removeEventListener("focusout", c, !1));
		};
	}, [e, t]), V(() => () => {
		r.current && cancelAnimationFrame(r.current);
	}, [r]);
}
function Na(e) {
	return Fa(e);
}
function Pa(e, t) {
	return !e || !t ? !1 : t.some((t) => R(t, e));
}
function Fa(e, t = null) {
	if (e instanceof Element && e.closest("[data-react-aria-top-layer]")) return !0;
	for (let { scopeRef: n } of Ya.traverse(Ya.getTreeNode(t))) if (n && Pa(e, n.current)) return !0;
	return !1;
}
function Ia(e) {
	return Fa(e, G);
}
function La(e, t) {
	let n = Ya.getTreeNode(t)?.parent;
	for (; n;) {
		if (n.scopeRef === e) return !0;
		n = n.parent;
	}
	return !1;
}
function Ra(e, t = !1) {
	if (e != null && !t) try {
		ir(e);
	} catch {}
	else if (e != null) try {
		e.focus();
	} catch {}
}
function za(e, t = !0) {
	let n = e[0].previousElementSibling, r = Oa(e), i = Ka(r, { tabbable: t }, e);
	i.currentNode = n;
	let a = i.nextNode();
	return t && !a && (r = Oa(e), i = Ka(r, { tabbable: !1 }, e), i.currentNode = n, a = i.nextNode()), a;
}
function Ba(e, t = !0) {
	Ra(za(e, t));
}
function Va(e, t) {
	let n = x.useRef(t);
	(0, x.useEffect)(() => {
		n.current && (G = e, !Pa(Ft(L(e.current ? e.current[0] : void 0)), G.current) && e.current && Ba(e.current)), n.current = !1;
	}, [e]);
}
function Ha(e, t, n) {
	V(() => {
		if (t || n) return;
		let r = e.current, i = L(r ? r[0] : void 0), a = (t) => {
			let n = z(t);
			Pa(n, e.current) ? G = e : Na(n) || (G = null);
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
function Ua(e) {
	let t = Ya.getTreeNode(G);
	for (; t && t.scopeRef !== e;) {
		if (t.nodeToRestore) return !1;
		t = t.parent;
	}
	return t?.scopeRef === e;
}
function Wa(e, t, n) {
	let r = (0, x.useRef)(typeof document < "u" ? Ft(L(e.current ? e.current[0] : void 0)) : null);
	V(() => {
		let r = e.current, i = L(r ? r[0] : void 0);
		if (!t || n) return;
		let a = () => {
			(!G || La(G, e)) && Pa(Ft(i), e.current) && (G = e);
		};
		return i.addEventListener("focusin", a, !1), r?.forEach((e) => e.addEventListener("focusin", a, !1)), () => {
			i.removeEventListener("focusin", a, !1), r?.forEach((e) => e.removeEventListener("focusin", a, !1));
		};
	}, [e, n]), V(() => {
		let r = L(e.current ? e.current[0] : void 0);
		if (!t) return;
		let i = (t) => {
			if (t.key !== "Tab" || t.altKey || t.ctrlKey || t.metaKey || !ka(e) || t.isComposing) return;
			let n = r.activeElement;
			if (!Fa(n, e) || !Ua(e)) return;
			let i = Ya.getTreeNode(e);
			if (!i) return;
			let a = i.nodeToRestore, o = Ka(r.body, { tabbable: !0 });
			o.currentNode = n;
			let s = t.shiftKey ? o.previousNode() : o.nextNode();
			if ((!a || !a.isConnected || a === r.body) && (a = void 0, i.nodeToRestore = void 0), (!s || !Fa(s, e)) && a) {
				o.currentNode = a;
				do
					s = t.shiftKey ? o.previousNode() : o.nextNode();
				while (Fa(s, e));
				t.preventDefault(), t.stopPropagation(), s ? Ra(s, !0) : Na(a) ? Ra(a, !0) : n.blur();
			}
		};
		return n || r.addEventListener("keydown", i, !0), () => {
			n || r.removeEventListener("keydown", i, !0);
		};
	}, [
		e,
		t,
		n
	]), V(() => {
		let n = L(e.current ? e.current[0] : void 0);
		if (!t) return;
		let i = Ya.getTreeNode(e);
		if (i) return i.nodeToRestore = r.current ?? void 0, () => {
			let r = Ya.getTreeNode(e);
			if (!r) return;
			let i = r.nodeToRestore, a = Ft(n);
			if (t && i && (a && Fa(a, e) || a === n.body && Ua(e))) {
				let t = Ya.clone();
				requestAnimationFrame(() => {
					if (n.activeElement === n.body) {
						let n = t.getTreeNode(e);
						for (; n;) {
							if (n.nodeToRestore && n.nodeToRestore.isConnected) {
								Ga(n.nodeToRestore);
								return;
							}
							n = n.parent;
						}
						for (n = t.getTreeNode(e); n;) {
							if (n.scopeRef && n.scopeRef.current && Ya.getTreeNode(n.scopeRef)) {
								let e = za(n.scopeRef.current, !0);
								if (e) {
									Ga(e);
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
function Ga(e) {
	e.dispatchEvent(new CustomEvent(Ta, {
		bubbles: !0,
		cancelable: !0
	})) && Ra(e);
}
function Ka(e, t, n) {
	let r = t?.tabbable ? Gt : Wt, i = L(e?.nodeType === Node.ELEMENT_NODE ? e : null), a = Ca(i, e || i, NodeFilter.SHOW_ELEMENT, { acceptNode(e) {
		return R(t?.from, e) || t?.tabbable && e.tagName === "INPUT" && e.getAttribute("type") === "radio" && (!ja(e) || a.currentNode.tagName === "INPUT" && a.currentNode.type === "radio" && a.currentNode.name === e.name) ? NodeFilter.FILTER_REJECT : r(e) && (!n || Pa(e, n)) && (!t?.accept || t.accept(e)) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
	} });
	return t?.from && (a.currentNode = t.from), a;
}
var qa = class e {
	constructor() {
		this.fastMap = /* @__PURE__ */ new Map(), this.root = new Ja({ scopeRef: null }), this.fastMap.set(null, this.root);
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
		let i = new Ja({ scopeRef: e });
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
		for (let e of this.traverse()) e !== t && t.nodeToRestore && e.nodeToRestore && t.scopeRef && t.scopeRef.current && Pa(e.nodeToRestore, t.scopeRef.current) && (e.nodeToRestore = t.nodeToRestore);
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
}, Ja = class {
	constructor(e) {
		this.children = /* @__PURE__ */ new Set(), this.contain = !1, this.scopeRef = e.scopeRef;
	}
	addChild(e) {
		this.children.add(e), e.parent = this;
	}
	removeChild(e) {
		this.children.delete(e), e.parent = void 0;
	}
}, Ya = new qa(), Xa = 7e3, Za = null;
function Qa(e, t = "assertive", n = Xa) {
	Za ? Za.announce(e, t, n) : (Za = new $a(), (typeof IS_REACT_ACT_ENVIRONMENT == "boolean" ? IS_REACT_ACT_ENVIRONMENT : typeof jest < "u") ? Za.announce(e, t, n) : setTimeout(() => {
		Za?.isAttached() && Za?.announce(e, t, n);
	}, 100));
}
var $a = class {
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
	announce(e, t = "assertive", n = Xa) {
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
function eo(e, t) {
	if (!e) return !1;
	let n = window.getComputedStyle(e), r = document.scrollingElement || document.documentElement, i = /(auto|scroll)/.test(n.overflow + n.overflowX + n.overflowY);
	return e === r && n.overflow !== "hidden" && (i = !0), i && t && (i = e.scrollHeight !== e.clientHeight || e.scrollWidth !== e.clientWidth), i;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getScrollParent.mjs
function to(e, t) {
	let n = e;
	for (eo(n, t) && (n = n.parentElement); n && !eo(n, t);) n = n.parentElement;
	return n || document.scrollingElement || document.documentElement;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/getScrollParents.mjs
function no(e, t) {
	let n = [], r = document.scrollingElement || document.documentElement;
	for (; e && (eo(e, t) && n.push(e), e !== r);) e = e.parentElement;
	return n;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/scrollIntoView.mjs
function ro(e, t, n = {}) {
	e !== t && io(e, t, t.getBoundingClientRect(), n);
}
function io(e, t, n, r = {}) {
	let { block: i = "nearest", inline: a = "nearest" } = r, o = e.scrollTop, s = e.scrollLeft, c = e.getBoundingClientRect(), l = window.getComputedStyle(t), u = window.getComputedStyle(e), d = document.scrollingElement || document.documentElement, f = e === d, p = e === d ? 0 : c.top, m = e === d ? e.clientHeight : c.bottom, h = e === d ? 0 : c.left, g = e === d ? e.clientWidth : c.right, _ = parseFloat(l.scrollMarginTop) || 0, v = parseFloat(l.scrollMarginBottom) || 0, y = parseFloat(l.scrollMarginLeft) || 0, b = parseFloat(l.scrollMarginRight) || 0, x = parseFloat(u.scrollPaddingTop) || 0, S = parseFloat(u.scrollPaddingBottom) || 0, C = parseFloat(u.scrollPaddingLeft) || 0, w = parseFloat(u.scrollPaddingRight) || 0, T = parseFloat(u.borderTopWidth) || 0, E = parseFloat(u.borderBottomWidth) || 0, D = parseFloat(u.borderLeftWidth) || 0, O = parseFloat(u.borderRightWidth) || 0, k = n.top - _, A = n.bottom + v, ee = n.left - y, j = n.right + b, te = e === d ? 0 : D + O, M = e === d ? 0 : T + E, ne = e === d ? 0 : e.offsetWidth - e.clientWidth - te, N = e === d ? 0 : e.offsetHeight - e.clientHeight - M, re = p + (f ? 0 : T) + x, P = m - (f ? 0 : E) - S - N, ie = h + (f ? 0 : D) + C, ae = g - (f ? 0 : O) - w;
	an() && sn() || u.direction === "ltr" ? ae -= ne : u.direction === "rtl" && (ie += ne);
	let oe = k < re || A > P, se = ee < ie || j > ae;
	if (oe && i === "start") o += k - re;
	else if (oe && i === "center") o += (k + A) / 2 - (re + P) / 2;
	else if (oe && i === "end") o += A - P;
	else if (oe && i === "nearest") {
		let e = k - re, t = A - P;
		o += Math.abs(e) <= Math.abs(t) ? e : t;
	}
	if (se && a === "start") s += ee - ie;
	else if (se && a === "center") s += (ee + j) / 2 - (ie + ae) / 2;
	else if (se && a === "end") s += j - ae;
	else if (se && a === "nearest") {
		let e = ee - ie, t = j - ae;
		s += Math.abs(e) <= Math.abs(t) ? e : t;
	}
	e.scrollTo({
		left: s,
		top: o
	});
}
function ao(e, t = {}) {
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
			let { left: t, top: r } = e.getBoundingClientRect(), i = no(e, !0);
			for (let t of i) ro(t, e);
			let { left: a, top: o } = e.getBoundingClientRect();
			if (Math.abs(t - a) > 1 || Math.abs(r - o) > 1) {
				i = n ? no(n, !0) : [];
				for (let e of i) ro(e, n, {
					block: "center",
					inline: "center"
				});
				for (let t of no(e, !0)) ro(t, e);
			}
		}
	}
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useDescription.mjs
var oo = 0, so = /* @__PURE__ */ new Map();
function co(e) {
	let [t, n] = (0, x.useState)();
	return V(() => {
		if (!e) return;
		let t = so.get(e);
		if (t) n(t.element.id);
		else {
			let r = `react-aria-description-${oo++}`;
			n(r);
			let i = document.createElement("div");
			i.id = r, i.style.display = "none", i.textContent = e, document.body.appendChild(i), t = {
				refCount: 0,
				element: i
			}, so.set(e, t);
		}
		return t.refCount++, () => {
			t && --t.refCount === 0 && (t.element.remove(), so.delete(e));
		};
	}, [e]), { "aria-describedby": e ? t : void 0 };
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useFormReset.mjs
function lo(e, t, n) {
	let r = yi((e) => {
		n && !e.defaultPrevented && n(t);
	});
	(0, x.useEffect)(() => {
		let t = e?.current?.form;
		return t?.addEventListener("reset", r), () => {
			t?.removeEventListener("reset", r);
		};
	}, [e]);
}
//#endregion
//#region node_modules/react-aria/dist/private/form/useFormValidation.mjs
function uo(e, t, n) {
	let { validationBehavior: r, focus: i } = e;
	V(() => {
		if (r === "native" && n?.current && "setCustomValidity" in n.current && !n.current.disabled) {
			let e = t.realtimeValidation.isInvalid ? t.realtimeValidation.validationErrors.join(" ") || "Invalid value." : "";
			n.current.setCustomValidity(e), n.current.hasAttribute("title") || (n.current.title = ""), t.realtimeValidation.isInvalid || t.updateValidation(po(n.current));
		}
	});
	let a = (0, x.useRef)(!1), o = yi(() => {
		a.current || t.resetValidation();
	}), s = yi((e) => {
		t.displayValidation.isInvalid || t.commitValidation();
		let r = n?.current?.form;
		!e.defaultPrevented && n && r && mo(r) === n.current && (i ? i() : n.current?.focus(), Yn("keyboard")), e.preventDefault();
	}), c = yi(() => {
		t.commitValidation();
	});
	(0, x.useEffect)(() => {
		let e = n?.current;
		if (!e) return;
		let t = e.form, r = t?.reset;
		return t && (t.reset = () => {
			a.current = !window.event || window.event.type === "message" && z(window.event) instanceof MessagePort, r?.call(t), a.current = !1;
		}), e.addEventListener("invalid", s), e.addEventListener("change", c), t?.addEventListener("reset", o), () => {
			e.removeEventListener("invalid", s), e.removeEventListener("change", c), t?.removeEventListener("reset", o), t && (t.reset = r);
		};
	}, [n, r]);
}
function fo(e) {
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
function po(e) {
	return {
		isInvalid: !e.validity.valid,
		validationDetails: fo(e),
		validationErrors: e.validationMessage ? [e.validationMessage] : []
	};
}
function mo(e) {
	for (let t = 0; t < e.elements.length; t++) {
		let n = e.elements[t];
		if (n.validity?.valid === !1) return n;
	}
	return null;
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useSlot.mjs
function ho(e = !0) {
	let [t, n] = (0, x.useState)(e), r = (0, x.useRef)(!1), i = (0, x.useCallback)((e) => {
		r.current = !0, n(!!e);
	}, []);
	return V(() => {
		r.current || n(!1);
	}, []), [i, t];
}
function go(e = !0) {
	let t = dr(), [n, r] = ho(e);
	return {
		id: r ? t : void 0,
		ref: n
	};
}
//#endregion
//#region node_modules/react-stately/dist/private/form/useFormValidationState.mjs
var _o = {
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
}, vo = {
	..._o,
	customError: !0,
	valid: !1
}, yo = {
	isInvalid: !1,
	validationDetails: _o,
	validationErrors: []
}, bo = (0, x.createContext)({}), xo = "__reactAriaFormValidationState";
function So(e) {
	if (e.__reactAriaFormValidationState) {
		let { realtimeValidation: t, displayValidation: n, updateValidation: r, resetValidation: i, commitValidation: a } = e[xo];
		return {
			realtimeValidation: t,
			displayValidation: n,
			updateValidation: r,
			resetValidation: i,
			commitValidation: a
		};
	}
	return Co(e);
}
function Co(e) {
	let { isInvalid: t, validationState: n, name: r, value: i, builtinValidation: a, validate: o, validationBehavior: s = "aria" } = e;
	n && (t ||= n === "invalid");
	let c = t === void 0 ? null : {
		isInvalid: t,
		validationErrors: [],
		validationDetails: vo
	}, l = (0, x.useMemo)(() => !o || i == null ? null : Eo(To(o, i)), [o, i]);
	a?.validationDetails.valid && (a = void 0);
	let u = (0, x.useContext)(bo), d = (0, x.useMemo)(() => r ? Array.isArray(r) ? r.flatMap((e) => wo(u[e])) : wo(u[r]) : [], [u, r]), [f, p] = (0, x.useState)(u), [m, h] = (0, x.useState)(!1);
	u !== f && (p(u), h(!1));
	let g = (0, x.useMemo)(() => Eo(m ? [] : d), [m, d]), _ = (0, x.useRef)(yo), [v, y] = (0, x.useState)(yo), b = (0, x.useRef)(yo), S = () => {
		if (!C) return;
		w(!1);
		let e = l || a || _.current;
		Do(e, b.current) || (b.current = e, y(e));
	}, [C, w] = (0, x.useState)(!1);
	return (0, x.useEffect)(S), {
		realtimeValidation: c || g || l || a || yo,
		displayValidation: s === "native" ? c || g || v : c || g || l || a || v,
		updateValidation(e) {
			s === "aria" && !Do(v, e) ? y(e) : _.current = e;
		},
		resetValidation() {
			let e = yo;
			Do(e, b.current) || (b.current = e, y(e)), s === "native" && w(!1), h(!0);
		},
		commitValidation() {
			s === "native" && w(!0), h(!0);
		}
	};
}
function wo(e) {
	return e ? Array.isArray(e) ? e : [e] : [];
}
function To(e, t) {
	if (typeof e == "function") {
		let n = e(t);
		if (n && typeof n != "boolean") return wo(n);
	}
	return [];
}
function Eo(e) {
	return e.length ? {
		isInvalid: !0,
		validationErrors: e,
		validationDetails: vo
	} : null;
}
function Do(e, t) {
	return e === t || !!e && !!t && e.isInvalid === t.isInvalid && e.validationErrors.length === t.validationErrors.length && e.validationErrors.every((e, n) => e === t.validationErrors[n]) && Object.entries(e.validationDetails).every(([e, n]) => t.validationDetails[e] === n);
}
//#endregion
//#region node_modules/react-aria/dist/private/toggle/useToggle.mjs
function Oo(e, t, n) {
	let { isDisabled: r = !1, isReadOnly: i = !1, value: a, name: o, form: s, children: c, isRequired: l, validationBehavior: u = "aria", "aria-label": d, "aria-labelledby": f, "aria-describedby": p, onPressStart: m, onPressEnd: h, onPressChange: g, onPress: _, onPressUp: v, onClick: y } = e, b = So({
		...e,
		value: t.isSelected
	}), { isInvalid: S, validationErrors: C, validationDetails: w } = b.displayValidation;
	uo(e, b, n);
	let T = (e) => {
		e.stopPropagation(), t.setSelected(z(e).checked);
	}, { pressProps: E, isPressed: D } = pa({
		onPressStart: m,
		onPressEnd: h,
		onPressChange: g,
		onPress: _,
		onPressUp: v,
		onClick: y,
		isDisabled: r
	}), [O, k] = (0, x.useState)(!1), { pressProps: A } = pa({
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
			let { [xo]: i } = e, { commitValidation: a } = i || b;
			a();
		},
		isDisabled: r || i
	}), { focusableProps: ee } = Lr(e, n), j = H(E, ee), te = U(e, { labelable: !0 });
	lo(n, t.defaultSelected, t.setSelected);
	let M = go(), ne = go();
	return {
		labelProps: H(A, { onClick: (e) => e.preventDefault() }),
		inputProps: H(te, {
			checked: t.isSelected,
			"aria-required": l && u === "aria" || void 0,
			required: l && u === "native",
			"aria-invalid": S || e.validationState === "invalid" || void 0,
			"aria-errormessage": e["aria-errormessage"],
			"aria-controls": e["aria-controls"],
			"aria-readonly": i || void 0,
			"aria-describedby": [
				M.id,
				ne.id,
				p
			].filter(Boolean).join(" ") || void 0,
			onChange: T,
			disabled: r,
			...a == null ? {} : { value: a },
			name: o,
			form: s,
			type: "checkbox",
			...j
		}),
		descriptionProps: M,
		errorMessageProps: ne,
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
function ko(e, t, n) {
	let { labelProps: r, inputProps: i, descriptionProps: a, errorMessageProps: o, isSelected: s, isPressed: c, isDisabled: l, isReadOnly: u, isInvalid: d, validationErrors: f, validationDetails: p } = Oo(e, t, n), { isIndeterminate: m } = e;
	return (0, x.useEffect)(() => {
		n.current && (n.current.indeterminate = !!m);
	}), {
		labelProps: H(r, (0, x.useMemo)(() => ({ onMouseDown: (e) => e.preventDefault() }), [])),
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
var Ao = /* @__PURE__ */ new WeakMap();
//#endregion
//#region node_modules/react-aria/dist/private/label/useLabel.mjs
function jo(e) {
	let { id: t, label: n, "aria-labelledby": r, "aria-label": i, labelElementType: a = "label" } = e;
	t = dr(t);
	let o = dr(), s = {};
	n && (r = r ? `${o} ${r}` : o, s = {
		id: o,
		htmlFor: a === "label" ? t : void 0
	});
	let c = xi({
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
function Mo(e) {
	let { description: t, errorMessage: n, isInvalid: r, validationState: i } = e, { labelProps: a, fieldProps: o } = jo(e), s = pr([
		!!t,
		!!n,
		r,
		i
	]), c = pr([
		!!t,
		!!n,
		r,
		i
	]);
	return o = H(o, { "aria-describedby": [
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
function No(e) {
	let { isDisabled: t, onBlurWithin: n, onFocusWithin: r, onFocusWithinChange: i } = e, a = (0, x.useRef)({ isFocusWithin: !1 }), { addGlobalListener: o, removeAllGlobalListeners: s } = sa(), c = (0, x.useCallback)((e) => {
		R(e.currentTarget, z(e)) && a.current.isFocusWithin && !R(e.currentTarget, e.relatedTarget) && (a.current.isFocusWithin = !1, s(), n && n(e), i && i(!1));
	}, [
		n,
		i,
		a,
		s
	]), l = Yt(c), u = (0, x.useCallback)((e) => {
		if (!R(e.currentTarget, z(e))) return;
		let t = z(e), n = L(t), s = Ft(n);
		if (!a.current.isFocusWithin && s === t) {
			r && r(e), i && i(!0), a.current.isFocusWithin = !0, l(e);
			let t = e.currentTarget;
			o(n, "focus", (e) => {
				let r = z(e);
				if (a.current.isFocusWithin && !R(t, r)) {
					let e = new n.defaultView.FocusEvent("blur", { relatedTarget: r });
					Jt(e, t);
					let i = qt(e);
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
var Po = typeof document < "u" ? x.useInsertionEffect ?? x.useLayoutEffect : () => {};
function Fo(e, t, n) {
	let [r, i] = (0, x.useState)(e || t), a = (0, x.useRef)(r), o = (0, x.useRef)(e !== void 0), s = e !== void 0;
	(0, x.useEffect)(() => {
		o.current, o.current = s;
	}, [s]);
	let c = s ? e : r;
	Po(() => {
		a.current = c;
	});
	let [, l] = (0, x.useReducer)(() => ({}), {});
	return [c, (0, x.useCallback)((e, ...t) => {
		let r = typeof e == "function" ? e(a.current) : e;
		Object.is(a.current, r) || (a.current = r, i(r), l(), n?.(r, ...t));
	}, [n])];
}
//#endregion
//#region node_modules/react-stately/dist/private/toggle/useToggleState.mjs
function Io(e = {}) {
	let { isReadOnly: t } = e, [n, r] = Fo(e.isSelected, e.defaultSelected || !1, e.onChange), [i] = (0, x.useState)(n);
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
function K(e, t, n) {
	let r = Io({
		isReadOnly: e.isReadOnly || t.isReadOnly,
		isSelected: t.isSelected(e.value),
		defaultSelected: t.defaultValue.includes(e.value),
		onChange(n) {
			n ? t.addValue(e.value) : t.removeValue(e.value), e.onChange && e.onChange(n);
		}
	}), { name: i, form: a, descriptionId: o, errorMessageId: s, validationBehavior: c } = Ao.get(t);
	c = e.validationBehavior ?? c;
	let { realtimeValidation: l } = So({
		...e,
		value: r.isSelected,
		name: void 0,
		validationBehavior: "aria"
	}), u = (0, x.useRef)(yo), d = () => {
		t.setInvalid(e.value, l.isInvalid ? l : u.current);
	};
	(0, x.useEffect)(d);
	let f = t.realtimeValidation.isInvalid ? t.realtimeValidation : l, p = c === "native" ? t.displayValidation : f, m = ko({
		...e,
		isReadOnly: e.isReadOnly || t.isReadOnly,
		isDisabled: e.isDisabled || t.isDisabled,
		name: e.name || i,
		form: e.form || a,
		isRequired: e.isRequired ?? t.isRequired,
		validationBehavior: c,
		[xo]: {
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
function Lo(e, t = -Infinity, n = Infinity) {
	return Math.min(Math.max(e, t), n);
}
//#endregion
//#region node_modules/react-aria/dist/private/visually-hidden/VisuallyHidden.mjs
var Ro = {
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
function zo(e = {}) {
	let { style: t, isFocusable: n } = e, [r, i] = (0, x.useState)(!1), { focusWithinProps: a } = No({
		isDisabled: !n,
		onFocusWithinChange: (e) => i(e)
	}), o = (0, x.useMemo)(() => r ? t : t ? {
		...Ro,
		...t
	} : Ro, [r]);
	return { visuallyHiddenProps: {
		...a,
		style: o
	} };
}
function Bo(e) {
	let { children: t, elementType: n = "div", isFocusable: r, style: i, ...a } = e, { visuallyHiddenProps: o } = zo(e);
	return /*#__PURE__*/ x.createElement(n, H(a, o), t);
}
//#endregion
//#region node_modules/react-aria/dist/private/textfield/useTextField.mjs
function Vo(e, t) {
	let { inputElementType: n = "input", isDisabled: r = !1, isRequired: i = !1, isReadOnly: a = !1, type: o = "text", validationBehavior: s = "aria" } = e, [c, l] = Fo(e.value, e.defaultValue || "", e.onChange), { focusableProps: u } = Lr(e, t), d = So({
		...e,
		value: c
	}), { isInvalid: f, validationErrors: p, validationDetails: m } = d.displayValidation, { labelProps: h, fieldProps: g, descriptionProps: _, errorMessageProps: v } = Mo({
		...e,
		isInvalid: f,
		errorMessage: e.errorMessage || p
	}), y = U(e, { labelable: !0 }), b = {
		type: o,
		pattern: e.pattern
	}, [S] = (0, x.useState)(c);
	return lo(t, e.defaultValue ?? S, l), uo(e, d, t), {
		labelProps: h,
		inputProps: H(y, n === "input" ? b : void 0, {
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
			onChange: (e) => l(z(e).value),
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
var Ho = typeof HTMLElement < "u" && "inert" in HTMLElement.prototype;
function Uo(e) {
	return e.dataset.liveAnnouncer === "true" || e.dataset.reactAriaTopLayer !== void 0;
}
var Wo = /* @__PURE__ */ new WeakMap(), Go = [];
function Ko(e, t) {
	let n = Et(e?.[0]), r = t instanceof n.Element ? { root: t } : t, i = r?.root ?? document.body, a = r?.shouldUseInert && Ho, o = new Set(e), s = /* @__PURE__ */ new Set(), c = (e) => a && e instanceof n.HTMLElement ? e.inert : e.getAttribute("aria-hidden") === "true", l = (e, t) => {
		a && e instanceof n.HTMLElement ? e.inert = t : t ? e.setAttribute("aria-hidden", "true") : (e.removeAttribute("aria-hidden"), e instanceof n.HTMLElement && (e.inert = !1));
	}, u = /* @__PURE__ */ new Set();
	if (Pt()) {
		let t = i.getRootNode();
		for (let n of e) {
			let e = n.getRootNode();
			for (; At(e) && e !== t;) u.add(e), e = e.host.getRootNode();
		}
	}
	let d = (e) => {
		for (let t of e.querySelectorAll("[data-live-announcer], [data-react-aria-top-layer]")) o.add(t);
		let t = (e) => {
			if (s.has(e) || o.has(e) || e.parentElement && s.has(e.parentElement) && e.parentElement.getAttribute("role") !== "row") return NodeFilter.FILTER_REJECT;
			for (let t of o) if (R(e, t)) return NodeFilter.FILTER_SKIP;
			return NodeFilter.FILTER_ACCEPT;
		}, n = Ca(L(e), e, NodeFilter.SHOW_ELEMENT, { acceptNode: t }), r = t(e);
		if (r === NodeFilter.FILTER_ACCEPT && f(e), r !== NodeFilter.FILTER_REJECT) {
			let e = n.nextNode();
			for (; e != null;) f(e), e = n.nextNode();
		}
	}, f = (e) => {
		let t = Wo.get(e) ?? 0;
		c(e) && t === 0 || (t === 0 && l(e, !0), s.add(e), Wo.set(e, t + 1));
	};
	Go.length && Go[Go.length - 1].disconnect(), d(i);
	let p = new MutationObserver((e) => {
		for (let t of e) if (t.type === "childList") {
			if (t.target.isConnected && ![...o, ...s].some((e) => R(e, t.target))) for (let e of t.addedNodes) (e instanceof HTMLElement || e instanceof SVGElement) && Uo(e) ? o.add(e) : e instanceof Element && d(e);
			if (Pt()) {
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
	if (Pt()) for (let e of u) {
		let t = new MutationObserver((e) => {
			for (let t of e) if (t.type === "childList") {
				if (t.target.isConnected && ![...o, ...s].some((e) => R(e, t.target))) for (let e of t.addedNodes) (e instanceof HTMLElement || e instanceof SVGElement) && Uo(e) ? o.add(e) : e instanceof Element && d(e);
				if (Pt()) {
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
	return Go.push(h), () => {
		if (p.disconnect(), Pt()) for (let e of m) e.disconnect();
		for (let e of s) {
			let t = Wo.get(e);
			t != null && (t === 1 ? (l(e, !1), Wo.delete(e)) : Wo.set(e, t - 1));
		}
		h === Go[Go.length - 1] ? (Go.pop(), Go.length && Go[Go.length - 1].observe()) : Go.splice(Go.indexOf(h), 1);
	};
}
function qo(e) {
	let t = Go[Go.length - 1];
	if (t && !t.visibleNodes.has(e)) return t.visibleNodes.add(e), () => {
		t.visibleNodes.delete(e);
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/utils.mjs
var Jo = /* @__PURE__ */ new WeakMap();
function Yo(e) {
	return typeof e == "string" ? e.replace(/\s*/g, "") : "" + e;
}
function Xo(e, t) {
	let n = Jo.get(e);
	if (!n) throw Error("Unknown list");
	return `${n.id}-option-${Yo(t)}`;
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/utils.mjs
function Zo(e) {
	return on() ? e.altKey : e.ctrlKey;
}
function Qo(e, t) {
	let n = `[data-key="${CSS.escape(String(t))}"]`, r = e.current?.dataset.collection;
	return r && (n = `[data-collection="${CSS.escape(r)}"]${n}`), e.current?.querySelector(n);
}
var $o = /* @__PURE__ */ new WeakMap();
function es(e) {
	let t = dr();
	return $o.set(e, t), t;
}
function ts(e) {
	return $o.get(e);
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/DOMLayoutDelegate.mjs
var ns = class {
	constructor(e) {
		this.ref = e;
	}
	getItemRect(e) {
		let t = this.ref.current;
		if (!t) return null;
		let n = e == null ? null : Qo(this.ref, e);
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
}, rs = class {
	constructor(...e) {
		if (e.length === 1) {
			let t = e[0];
			this.collection = t.collection, this.ref = t.ref, this.collator = t.collator, this.disabledKeys = t.disabledKeys || /* @__PURE__ */ new Set(), this.disabledBehavior = t.disabledBehavior || "all", this.orientation = t.orientation || "vertical", this.direction = t.direction, this.layout = t.layout || "stack", this.layoutDelegate = t.layoutDelegate || new ns(t.ref);
		} else this.collection = e[0], this.disabledKeys = e[1], this.ref = e[2], this.collator = e[3], this.layout = "stack", this.orientation = "vertical", this.disabledBehavior = "all", this.layoutDelegate = new ns(this.ref);
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
		let t = this.getNextKey(e), n = Qo(this.ref, e);
		if (t != null) {
			let e = Qo(this.ref, t);
			return !n || !e ? !1 : n.getBoundingClientRect().top > e.getBoundingClientRect().top;
		}
		let r = this.getPreviousKey(e);
		if (r != null) {
			let e = Qo(this.ref, r);
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
		if (t && !eo(t)) return this.getFirstKey();
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
		if (t && !eo(t)) return this.getLastKey();
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
}, is = {};
is = { longPressMessage: "اضغط مطولاً أو اضغط على Alt + السهم لأسفل لفتح القائمة" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/bg-BG.mjs
var as = {};
as = { longPressMessage: "Натиснете продължително или натиснете Alt+ стрелка надолу, за да отворите менюто" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/cs-CZ.mjs
var os = {};
os = { longPressMessage: "Dlouhým stiskem nebo stisknutím kláves Alt + šipka dolů otevřete nabídku" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/da-DK.mjs
var ss = {};
ss = { longPressMessage: "Langt tryk eller tryk på Alt + pil ned for at åbne menuen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/de-DE.mjs
var cs = {};
cs = { longPressMessage: "Drücken Sie lange oder drücken Sie Alt + Nach-unten, um das Menü zu öffnen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/el-GR.mjs
var ls = {};
ls = { longPressMessage: "Πιέστε παρατεταμένα ή πατήστε Alt + κάτω βέλος για να ανοίξετε το μενού" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/en-US.mjs
var us = {};
us = { longPressMessage: "Long press or press Alt + ArrowDown to open menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/es-ES.mjs
var ds = {};
ds = { longPressMessage: "Mantenga pulsado o pulse Alt + flecha abajo para abrir el menú" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/et-EE.mjs
var fs = {};
fs = { longPressMessage: "Menüü avamiseks vajutage pikalt või vajutage klahve Alt + allanool" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/fi-FI.mjs
var ps = {};
ps = { longPressMessage: "Avaa valikko painamalla pohjassa tai näppäinyhdistelmällä Alt + Alanuoli" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/fr-FR.mjs
var ms = {};
ms = { longPressMessage: "Appuyez de manière prolongée ou appuyez sur Alt\xA0+\xA0Flèche vers le bas pour ouvrir le menu." };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/he-IL.mjs
var hs = {};
hs = { longPressMessage: "לחץ לחיצה ארוכה או הקש Alt + ArrowDown כדי לפתוח את התפריט" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/hr-HR.mjs
var gs = {};
gs = { longPressMessage: "Dugo pritisnite ili pritisnite Alt + strelicu prema dolje za otvaranje izbornika" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/hu-HU.mjs
var _s = {};
_s = { longPressMessage: "Nyomja meg hosszan, vagy nyomja meg az Alt + lefele nyíl gombot a menü megnyitásához" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/it-IT.mjs
var vs = {};
vs = { longPressMessage: "Premi a lungo o premi Alt + Freccia giù per aprire il menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ja-JP.mjs
var ys = {};
ys = { longPressMessage: "長押しまたは Alt+下矢印キーでメニューを開く" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ko-KR.mjs
var bs = {};
bs = { longPressMessage: "길게 누르거나 Alt + 아래쪽 화살표를 눌러 메뉴 열기" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/lt-LT.mjs
var xs = {};
xs = { longPressMessage: "Norėdami atidaryti meniu, nuspaudę palaikykite arba paspauskite „Alt + ArrowDown“." };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/lv-LV.mjs
var Ss = {};
Ss = { longPressMessage: "Lai atvērtu izvēlni, turiet nospiestu vai nospiediet taustiņu kombināciju Alt + lejupvērstā bultiņa" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/nb-NO.mjs
var Cs = {};
Cs = { longPressMessage: "Langt trykk eller trykk Alt + PilNed for å åpne menyen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/nl-NL.mjs
var ws = {};
ws = { longPressMessage: "Druk lang op Alt + pijl-omlaag of druk op Alt om het menu te openen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/pl-PL.mjs
var Ts = {};
Ts = { longPressMessage: "Naciśnij i przytrzymaj lub naciśnij klawisze Alt + Strzałka w dół, aby otworzyć menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/pt-BR.mjs
var Es = {};
Es = { longPressMessage: "Pressione e segure ou pressione Alt + Seta para baixo para abrir o menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/pt-PT.mjs
var Ds = {};
Ds = { longPressMessage: "Prima continuamente ou prima Alt + Seta Para Baixo para abrir o menu" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ro-RO.mjs
var Os = {};
Os = { longPressMessage: "Apăsați lung sau apăsați pe Alt + săgeată în jos pentru a deschide meniul" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/ru-RU.mjs
var ks = {};
ks = { longPressMessage: "Нажмите и удерживайте или нажмите Alt + Стрелка вниз, чтобы открыть меню" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sk-SK.mjs
var As = {};
As = { longPressMessage: "Ponuku otvoríte dlhým stlačením alebo stlačením klávesu Alt + klávesu so šípkou nadol" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sl-SI.mjs
var js = {};
js = { longPressMessage: "Za odprtje menija pritisnite in držite gumb ali pritisnite Alt+puščica navzdol" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sr-SP.mjs
var Ms = {};
Ms = { longPressMessage: "Dugo pritisnite ili pritisnite Alt + strelicu prema dole da otvorite meni" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/sv-SE.mjs
var Ns = {};
Ns = { longPressMessage: "Håll nedtryckt eller tryck på Alt + pil nedåt för att öppna menyn" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/tr-TR.mjs
var Ps = {};
Ps = { longPressMessage: "Menüyü açmak için uzun basın veya Alt + Aşağı Ok tuşuna basın" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/uk-UA.mjs
var Fs = {};
Fs = { longPressMessage: "Довго або звичайно натисніть комбінацію клавіш Alt і стрілка вниз, щоб відкрити меню" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/zh-CN.mjs
var Is = {};
Is = { longPressMessage: "长按或按 Alt + 向下方向键以打开菜单" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/menu/zh-TW.mjs
var Ls = {};
Ls = { longPressMessage: "長按或按 Alt+向下鍵以開啟功能表" };
//#endregion
//#region node_modules/react-aria/dist/private/menu/intlStrings.mjs
var Rs = {};
Rs = {
	"ar-AE": is,
	"bg-BG": as,
	"cs-CZ": os,
	"da-DK": ss,
	"de-DE": cs,
	"el-GR": ls,
	"en-US": us,
	"es-ES": ds,
	"et-EE": fs,
	"fi-FI": ps,
	"fr-FR": ms,
	"he-IL": hs,
	"hr-HR": gs,
	"hu-HU": _s,
	"it-IT": vs,
	"ja-JP": ys,
	"ko-KR": bs,
	"lt-LT": xs,
	"lv-LV": Ss,
	"nb-NO": Cs,
	"nl-NL": ws,
	"pl-PL": Ts,
	"pt-BR": Es,
	"pt-PT": Ds,
	"ro-RO": Os,
	"ru-RU": ks,
	"sk-SK": As,
	"sl-SI": js,
	"sr-SP": Ms,
	"sv-SE": Ns,
	"tr-TR": Ps,
	"uk-UA": Fs,
	"zh-CN": Is,
	"zh-TW": Ls
};
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useLongPress.mjs
var zs = 500;
function Bs(e) {
	let { isDisabled: t, pointerType: n, onLongPressStart: r, onLongPressEnd: i, onLongPress: a, threshold: o = zs, accessibilityDescription: s } = e, c = (0, x.useRef)(void 0), { addGlobalListener: l, removeAllGlobalListeners: u } = sa(), d = (e) => n ? e.pointerType === n : e.pointerType === "mouse" || e.pointerType === "touch", { pressProps: f } = pa({
		isDisabled: t,
		onPressStart(e) {
			if (e.continuePropagation(), d(e)) {
				r && r({
					...e,
					type: "longpressstart"
				}), c.current = setTimeout(() => {
					e.target.dispatchEvent(new PointerEvent("pointercancel", { bubbles: !0 })), l(e.target, "click", (e) => e.preventDefault(), { once: !0 }), L(e.target).activeElement !== e.target && xt(e.target), a && a({
						...e,
						type: "longpress"
					}), c.current = void 0;
				}, o), e.pointerType === "touch" && l(e.target, "contextmenu", (e) => e.preventDefault(), { once: !0 });
				let t = Et(e.target);
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
	return { longPressProps: H(f, co(a && !t ? s : void 0)) };
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useContextMenu.mjs
function Vs(e) {
	let { onContextMenu: t } = e, n = (0, x.useRef)(!1), { longPressProps: r } = Bs({
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
	return t ? { contextMenuProps: H(an() ? r : {}, {
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
			if (tn() && e.ctrlKey && e.key === "Enter") {
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
var Hs = /* @__PURE__ */ new WeakMap();
function Us(e) {
	let { triggerRef: t, isOpen: n, onClose: r } = e;
	(0, x.useEffect)(() => !n || r === null ? void 0 : jt(It(t.current), "scroll", (e) => {
		let n = z(e);
		if (!t.current || n instanceof Node && !R(n, t.current) || n instanceof HTMLInputElement || n instanceof HTMLTextAreaElement) return;
		let i = r || Hs.get(t.current);
		i && i();
	}, !0), [
		n,
		r,
		t
	]);
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/useOverlayTrigger.mjs
function Ws(e, t, n) {
	let { type: r } = e, { isOpen: i } = t;
	(0, x.useEffect)(() => {
		n && n.current && Hs.set(n.current, t.close);
	});
	let a;
	r === "menu" ? a = !0 : r === "listbox" && (a = "listbox");
	let o = dr();
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
function Gs(e) {
	return e && e.__esModule ? e.default : e;
}
function Ks(e, t, n) {
	let { type: r = "menu", isDisabled: i, trigger: a = "press" } = e, o = dr(), { triggerProps: s, overlayProps: c } = Ws({ type: r }, t, n), l = (e, n, r = "first") => {
		if (!e || n.isDefaultPrevented()) return !1;
		t.toggle(r);
	}, { keyboardProps: u } = Mr({
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
	}), d = Ki(Gs(Rs), "@react-aria/menu"), { longPressProps: f } = Bs({
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
			e.pointerType !== "touch" && e.pointerType !== "keyboard" && !i && (xt(e.target), t.open(e.pointerType === "virtual" ? "first" : null));
		},
		onPress(e) {
			e.pointerType === "touch" && !i && (xt(e.target), t.toggle());
		}
	};
	delete s.onPress;
	let { contextMenuProps: m } = Vs({ onContextMenu(e) {
		let n = e.target.getBoundingClientRect();
		t.setPoint({
			x: n.x + e.x,
			y: n.y + e.y
		}), t.open();
	} });
	(0, x.useEffect)(() => {
		if (t.isOpen && a === "contextMenu") {
			let e = (e) => {
				(e.button === 2 || e.button === 0 && e.ctrlKey === !0) && z(e) === document.body && t.close();
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
var qs = 1e3;
function Js(e) {
	let { keyboardDelegate: t, selectionManager: n, onTypeSelect: r } = e, i = (0, x.useRef)({
		search: "",
		timeout: void 0
	});
	return (0, x.useEffect)(() => {
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
				}, qs);
			}
		} : void 0,
		onKeyDown: t.getKeyForSearch ? (e) => {
			let a = Ys(e.key);
			if (!(!a || e.ctrlKey || e.metaKey || e.altKey || !R(e.currentTarget, z(e)) || i.current.search.length === 0 && a === " ")) {
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
				}, qs);
			}
		} : void 0
	} };
}
function Ys(e) {
	return e.length === 1 || !/^[A-Z]/i.test(e) ? e : "";
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useUpdateLayoutEffect.mjs
function Xs(e, t) {
	let n = (0, x.useRef)(!0), r = (0, x.useRef)(null);
	V(() => (n.current = !0, () => {
		n.current = !1;
	}), []), V(() => {
		n.current ? n.current = !1 : (!r.current || t.some((e, t) => !Object.is(e, r[t]))) && e(), r.current = t;
	}, t);
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useSelectableCollection.mjs
function Zs(e) {
	let { selectionManager: t, keyboardDelegate: n, ref: r, autoFocus: i = !1, shouldFocusWrap: a = !1, disallowEmptySelection: o = !1, disallowSelectAll: s = !1, escapeKeyBehavior: c = "clearSelection", selectOnFocus: l = t.selectionBehavior === "replace", disallowTypeAhead: u = !1, shouldUseVirtualFocus: d, allowsTabNavigation: f = !1, scrollRef: p = r, linkBehavior: m = "action", UNSTABLE_focusOnEntry: h } = e, { direction: g } = Mi(), _ = mn(), v = (e, n, i) => {
		if (n != null) {
			if (t.isLink(n) && m === "selection" && l && !Zo(e)) {
				(0, Kr.flushSync)(() => {
					t.setFocusedKey(n, i);
				});
				let a = Qo(r, n), o = t.getItemProps(n);
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
			if (l && !Zo(e)) {
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
	}, b = (e) => {
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
			let r = n.getFirstKey(t.focusedKey, hi(e));
			if (t.setFocusedKey(r), r != null) {
				if (hi(e) && e.shiftKey && t.selectionMode === "multiple") {
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
			let r = n.getLastKey(t.focusedKey, hi(e));
			if (t.setFocusedKey(r), r != null) {
				if (hi(e) && e.shiftKey && t.selectionMode === "multiple") {
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
			let e = Ka(r.current, { tabbable: !0 }), t, n;
			do
				n = e.lastChild(), n && (t = n);
			while (n);
			let i = Ft();
			t && (!Lt(t) || i && !Gt(i)) && xt(t);
		}
		return {
			shouldContinuePropagation: !0,
			shouldPreventDefault: !1
		};
	}, ee = () => (!f && r.current && r.current.focus(), {
		shouldContinuePropagation: !0,
		shouldPreventDefault: !1
	}), j = (e, t) => ({
		[tn() ? e + "+Shift+Alt" : e + "+Shift+Control"]: t,
		[e + "+Shift"]: t,
		[tn() ? e + "+Alt" : e + "+Control"]: t,
		[e]: t
	}), { keyboardProps: te } = Mr({
		shortcuts: {
			...j("ArrowDown", y),
			...j("ArrowUp", b),
			...j("ArrowLeft", C),
			...j("ArrowRight", w),
			...j("PageDown", E),
			...j("PageUp", D)
		},
		allowRepeats: !0
	}), { keyboardProps: M } = Mr({ shortcuts: {
		...j("Home", S),
		...j("End", T),
		"Mod+A": O,
		Escape: k,
		Tab: A,
		"Tab+Shift": ee
	} }), ne = (0, x.useRef)({
		top: 0,
		left: 0
	});
	bi(p, "scroll", () => {
		ne.current = {
			top: p.current?.scrollTop ?? 0,
			left: p.current?.scrollLeft ?? 0
		};
	});
	let N = (e) => {
		if (t.isFocused) {
			R(e.currentTarget, z(e)) || t.setFocused(!1);
			return;
		}
		if (!R(e.currentTarget, z(e))) return;
		let i = Jn();
		t.setFocused(!0);
		let a = (e) => {
			e != null && (t.setFocusedKey(e), l && !t.isSelected(e) && t.replaceSelection(e));
		};
		if (h && (i === "keyboard" || i === "virtual")) a(h === "first" ? n.getFirstKey?.() : n.getLastKey?.());
		else if (t.focusedKey == null) {
			let r = e.relatedTarget;
			r && e.currentTarget.compareDocumentPosition(r) & Node.DOCUMENT_POSITION_FOLLOWING ? a(t.lastSelectedKey ?? n.getLastKey?.()) : a(t.firstSelectedKey ?? n.getFirstKey?.());
		} else p.current && (p.current.scrollTop = ne.current.top, p.current.scrollLeft = ne.current.left);
		if (t.focusedKey != null && p.current) {
			let e = Qo(r, t.focusedKey);
			e instanceof HTMLElement && (!Lt(e) && !d && xt(e), (i === "keyboard" || h && i === "virtual") && ao(e, { containingElement: r.current }));
		}
	}, re = (e) => {
		R(e.currentTarget, e.relatedTarget) || t.setFocused(!1);
	}, P = (0, x.useRef)(!1);
	bi(r, ui, d ? (e) => {
		let { detail: n } = e;
		e.stopPropagation(), t.setFocused(!0), n?.focusStrategy === "first" && (P.current = !0);
	} : void 0);
	let ie = n.getFirstKey?.() ?? null;
	Xs(() => {
		if (P.current) {
			if (ie == null) {
				let e = Ft();
				di(r.current), pi(e, null), t.collection.size > 0 && (P.current = !1);
			} else t.setFocusedKey(ie), P.current = !1;
		}
	}, [ie, t.collection.size]), Xs(() => {
		t.collection.size > 0 && (P.current = !1);
	}, [t.focusedKey]), bi(r, li, d ? (e) => {
		e.stopPropagation(), t.setFocused(!1), e.detail?.clearFocusKey && t.setFocusedKey(null);
	} : void 0);
	let ae = (0, x.useRef)(i), oe = (0, x.useRef)(!1);
	(0, x.useEffect)(() => {
		if (ae.current) {
			let e = null;
			i === "first" && (e = n.getFirstKey?.() ?? null), i === "last" && (e = n.getLastKey?.() ?? null);
			let a = t.selectedKeys;
			if (a.size) {
				for (let n of a) if (t.canSelectItem(n)) {
					e = n;
					break;
				}
			}
			t.setFocused(!0), t.setFocusedKey(e), e != null && l && !a.size && t.canSelectItem(e) && t.replaceSelection(e), e == null && !d && r.current && ir(r.current), t.collection.size > 0 && (ae.current = !1, oe.current = !0);
		}
	});
	let se = (0, x.useRef)(t.focusedKey), ce = (0, x.useRef)(null);
	(0, x.useEffect)(() => {
		if (t.isFocused && t.focusedKey != null && (t.focusedKey !== se.current || oe.current) && p.current && r.current) {
			let e = Jn(), n = Qo(r, t.focusedKey);
			if (!(n instanceof HTMLElement)) return;
			(e === "keyboard" || oe.current) && (ce.current && cancelAnimationFrame(ce.current), ce.current = requestAnimationFrame(() => {
				p.current && (ro(p.current, n), e !== "virtual" && ao(n, { containingElement: r.current }));
			}));
		}
		!d && t.isFocused && t.focusedKey == null && se.current != null && r.current && ir(r.current), se.current = t.focusedKey, oe.current = !1;
	}), (0, x.useEffect)(() => () => {
		ce.current && cancelAnimationFrame(ce.current);
	}, []), bi(r, "react-aria-focus-scope-restore", (e) => {
		e.preventDefault(), t.setFocused(!0);
	});
	let le = {
		...H(M, te),
		onFocus: N,
		onBlur: re,
		onMouseDown(e) {
			p.current === z(e) && e.preventDefault();
		}
	}, { typeSelectProps: ue } = Js({
		keyboardDelegate: n,
		selectionManager: t
	});
	u || (le = H(ue, le));
	let de;
	d || (de = t.focusedKey == null ? 0 : -1);
	let fe = es(t.collection);
	return { collectionProps: H(le, {
		tabIndex: de,
		"data-collection": fe
	}) };
}
//#endregion
//#region node_modules/react-stately/dist/private/collections/getChildNodes.mjs
function Qs(e, t) {
	return typeof t.getChildren == "function" ? t.getChildren(e.key) : e.childNodes;
}
function $s(e) {
	return ec(e, 0);
}
function ec(e, t) {
	if (t < 0) return;
	let n = 0;
	for (let r of e) {
		if (n === t) return r;
		n++;
	}
}
function tc(e, t, n) {
	if (t.parentKey === n.parentKey) return t.index - n.index;
	let r = [...nc(e, t), t], i = [...nc(e, n), n], a = r.slice(0, i.length).findIndex((e, t) => e !== i[t]);
	return a === -1 ? r.findIndex((e) => e === n) >= 0 ? 1 : (i.findIndex((e) => e === t), -1) : (t = r[a], n = i[a], t.index - n.index);
}
function nc(e, t) {
	let n = [], r = t;
	for (; r?.parentKey != null;) r = e.getItem(r.parentKey), r && n.unshift(r);
	return n;
}
//#endregion
//#region node_modules/react-stately/dist/private/collections/getItemCount.mjs
var rc = /* @__PURE__ */ new WeakMap();
function ic(e) {
	let t = rc.get(e);
	if (t != null) return t;
	let n = 0, r = (t) => {
		for (let i of t) i.type === "section" ? r(Qs(i, e)) : i.type === "item" && n++;
	};
	return r(e), rc.set(e, n), n;
}
//#endregion
//#region node_modules/react-aria/dist/private/i18n/useCollator.mjs
var ac = /* @__PURE__ */ new Map();
function oc(e) {
	let { locale: t } = Mi(), n = t + (e ? Object.entries(e).sort((e, t) => e[0] < t[0] ? -1 : 1).join() : "");
	if (ac.has(n)) return ac.get(n);
	let r = new Intl.Collator(t, e);
	return ac.set(n, r), r;
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/PressResponder.mjs
function sc({ children: e }) {
	let t = (0, x.useMemo)(() => ({ register: () => {} }), []);
	return /*#__PURE__*/ x.createElement(oa.Provider, { value: t }, e);
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/PortalProvider.mjs
var cc = /*#__PURE__*/ (0, x.createContext)({});
function lc(e) {
	let { getContainer: t } = e, { getContainer: n } = uc();
	return /*#__PURE__*/ x.createElement(cc.Provider, { value: { getContainer: t === null ? void 0 : t ?? n } }, e.children);
}
function uc() {
	return (0, x.useContext)(cc) ?? {};
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/Overlay.mjs
var dc = /*#__PURE__*/ x.createContext(null);
function fc(e) {
	let t = An(), { portalContainer: n = t ? null : document.body, isExiting: r } = e, [i, a] = (0, x.useState)(!1), o = (0, x.useMemo)(() => ({
		contain: i,
		setContain: a
	}), [i, a]), { getContainer: s } = uc();
	if (!e.portalContainer && s && (n = s()), !n) return null;
	let c = e.children;
	return e.disableFocusManagement || (c = /*#__PURE__*/ x.createElement(Ea, {
		restoreFocus: !0,
		contain: (e.shouldContainFocus || i) && !r
	}, c)), c = /*#__PURE__*/ x.createElement(dc.Provider, { value: o }, /*#__PURE__*/ x.createElement(sc, null, /*#__PURE__*/ x.createElement(Fr.Provider, { value: null }, c))), /*#__PURE__*/ Kr.createPortal(c, n);
}
function pc() {
	let e = (0, x.useContext)(dc)?.setContain;
	V(() => {
		e?.(!0);
	}, [e]);
}
//#endregion
//#region node_modules/react-aria/dist/private/dialog/useDialog.mjs
function mc(e, t) {
	let { role: n = "dialog" } = e, r = pr();
	r = e["aria-label"] ? void 0 : r;
	let i = pr();
	i = n === "alertdialog" && !e["aria-describedby"] ? i : void 0;
	let a = (0, x.useRef)(!1);
	(0, x.useEffect)(() => {
		if (t.current && !Lt(t.current)) {
			ir(t.current);
			let e = setTimeout(() => {
				(Ft() === t.current || Ft() === document.body) && (a.current = !0, t.current && (t.current.blur(), ir(t.current)), a.current = !1);
			}, 500);
			return () => {
				clearTimeout(e);
			};
		}
	}, [t]), pc(), (0, x.useRef)(!1), (0, x.useEffect)(() => {});
	let o = e["aria-describedby"] ?? i;
	return {
		dialogProps: {
			...U(e, { labelable: !0 }),
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
function hc(e = {}) {
	let { autoFocus: t = !1, isTextInput: n, within: r } = e, i = (0, x.useRef)({
		isFocused: !1,
		isFocusVisible: t || qn()
	}), [a, o] = (0, x.useState)(!1), [s, c] = (0, x.useState)(() => i.current.isFocused && i.current.isFocusVisible), l = (0, x.useCallback)(() => c(i.current.isFocused && i.current.isFocusVisible), []), u = (0, x.useCallback)((e) => {
		i.current.isFocused = e, i.current.isFocusVisible = qn(), o(e), l();
	}, [l]);
	Qn((e) => {
		i.current.isFocusVisible = e, l();
	}, [n, a], {
		enabled: a,
		isTextInput: n
	});
	let { focusProps: d } = vr({
		isDisabled: r,
		onFocusChange: u
	}), { focusWithinProps: f } = No({
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
function gc(e = {}) {
	let { locale: t } = Mi();
	return (0, x.useMemo)(() => new Intl.ListFormat(t, e), [t, e]);
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useHover.mjs
var _c = !1, vc = 0;
function yc() {
	_c = !0, setTimeout(() => {
		_c = !1;
	}, 500);
}
function bc(e) {
	e.pointerType === "touch" && yc();
}
function xc() {
	let e = L(null);
	if (e !== void 0) return vc === 0 && typeof PointerEvent < "u" && e.addEventListener("pointerup", bc), vc++, () => {
		vc--, !(vc > 0) && typeof PointerEvent < "u" && e.removeEventListener("pointerup", bc);
	};
}
function Sc(e) {
	let { onHoverStart: t, onHoverChange: n, onHoverEnd: r, isDisabled: i } = e, [a, o] = (0, x.useState)(!1), s = (0, x.useRef)({
		isHovered: !1,
		ignoreEmulatedMouseEvents: !1,
		pointerType: "",
		target: null
	}).current;
	(0, x.useEffect)(xc, []);
	let { addGlobalListener: c, removeAllGlobalListeners: l } = sa(), { hoverProps: u, triggerHoverEnd: d } = (0, x.useMemo)(() => {
		let e = (e, r) => {
			if (s.pointerType = r, i || r === "touch" || s.isHovered || !R(e.currentTarget, z(e))) return;
			s.isHovered = !0;
			let l = e.currentTarget;
			s.target = l, c(L(z(e)), "pointerover", (e) => {
				s.isHovered && s.target && !R(s.target, z(e)) && a(e, e.pointerType);
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
			_c && t.pointerType === "mouse" || e(t, t.pointerType);
		}, u.onPointerLeave = (e) => {
			!i && R(e.currentTarget, z(e)) && a(e, e.pointerType);
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
	return (0, x.useEffect)(() => {
		i && d({ currentTarget: s.target }, s.pointerType);
	}, [i]), {
		hoverProps: u,
		isHovered: a
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/interactions/useInteractOutside.mjs
function Cc(e) {
	let { ref: t, onInteractOutside: n, isDisabled: r, onInteractOutsideStart: i } = e, a = (0, x.useRef)({
		isPointerDown: !1,
		ignoreEmulatedMouseEvents: !1
	}), o = yi((e) => {
		n && wc(e, t) && (i && i(e), a.current.isPointerDown = !0);
	}), s = yi((e) => {
		n && n(e);
	});
	(0, x.useEffect)(() => {
		let e = a.current;
		if (r) return;
		let n = t.current, i = L(n);
		if (typeof PointerEvent < "u") {
			let n = (n) => {
				e.isPointerDown && wc(n, t) && s(n), e.isPointerDown = !1;
			};
			return i.addEventListener("pointerdown", o, !0), i.addEventListener("click", n, !0), () => {
				i.removeEventListener("pointerdown", o, !0), i.removeEventListener("click", n, !0);
			};
		}
	}, [t, r]);
}
function wc(e, t) {
	if (e.button > 0) return !1;
	let n = z(e);
	if (n) {
		let e = n.ownerDocument;
		if (!e || !R(e.documentElement, n) || n.closest("[data-react-aria-top-layer]")) return !1;
	}
	return t.current ? !e.composedPath().includes(t.current) : !1;
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useSelectableList.mjs
function Tc(e) {
	let { selectionManager: t, collection: n, disabledKeys: r, ref: i, keyboardDelegate: a, layoutDelegate: o, orientation: s } = e, c = oc({
		usage: "search",
		sensitivity: "base"
	}), l = t.disabledBehavior, u = (0, x.useMemo)(() => a || new rs({
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
	]), { collectionProps: d } = Zs({
		...e,
		ref: i,
		selectionManager: t,
		keyboardDelegate: u
	});
	return { listProps: d };
}
//#endregion
//#region node_modules/react-aria/dist/private/selection/useSelectableItem.mjs
function Ec(e) {
	let { id: t, selectionManager: n, key: r, ref: i, shouldSelectOnPressUp: a, shouldUseVirtualFocus: o, focus: s, isDisabled: c, onAction: l, allowsDifferentPressOrigin: u, linkBehavior: d = "action" } = e, f = mn();
	t = dr(t);
	let p = (e) => {
		if (e.pointerType === "keyboard" && Zo(e)) n.toggleSelection(r);
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
			n.selectionMode === "single" ? n.isSelected(r) && !n.disallowEmptySelection ? n.toggleSelection(r) : n.replaceSelection(r) : e && e.shiftKey ? n.extendSelection(r) : n.selectionBehavior === "toggle" || e && (hi(e) || e.pointerType === "touch" || e.pointerType === "virtual") ? n.toggleSelection(r) : n.replaceSelection(r);
		}
	};
	(0, x.useEffect)(() => {
		r === n.focusedKey && n.isFocused && (o ? di(i.current) : s ? s() : Ft() !== i.current && i.current && ir(i.current));
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
			z(e) === i.current && n.setFocusedKey(r);
		}
	} : c && (m.onMouseDown = (e) => {
		e.preventDefault();
	}), (0, x.useEffect)(() => {
		c && n.focusedKey === r && n.setFocusedKey(null);
	}, [
		n,
		c,
		r
	]);
	let h = n.isLink(r) && d === "override", g = l && e.UNSTABLE_itemBehavior === "action", _ = n.isLink(r) && d !== "selection" && d !== "none", v = !c && n.canSelectItem(r) && !h && !g, y = (l || _) && !c, b = y && (n.selectionBehavior === "replace" ? !v : !v || n.isEmpty), S = y && v && n.selectionBehavior === "replace", C = b || S, w = (0, x.useRef)(null), T = C && v, E = (0, x.useRef)(!1), D = (0, x.useRef)(!1), O = n.getItemProps(r), k = (e) => {
		l && (l(), i.current?.dispatchEvent(new CustomEvent("react-aria-item-action", { bubbles: !0 }))), _ && i.current && f.open(i.current, e, O.href, O.routerOptions);
	}, A = { ref: i };
	a ? (A.onPressStart = (e) => {
		w.current = e.pointerType, E.current = T, e.pointerType === "keyboard" && (!C || Oc(e.key)) && p(e);
	}, u ? (A.onPressUp = b ? void 0 : (e) => {
		e.pointerType === "mouse" && v && p(e);
	}, A.onPress = b ? k : (e) => {
		e.pointerType !== "keyboard" && e.pointerType !== "mouse" && v && p(e);
	}) : A.onPress = (e) => {
		if (b || S && e.pointerType !== "mouse") {
			if (e.pointerType === "keyboard" && !Dc(e.key)) return;
			k(e);
		} else e.pointerType !== "keyboard" && v && p(e);
	}) : (A.onPressStart = (e) => {
		w.current = e.pointerType, E.current = T, D.current = b, v && (e.pointerType === "mouse" && !b || e.pointerType === "keyboard" && (!y || Oc(e.key))) && p(e);
	}, A.onPress = (e) => {
		(e.pointerType === "touch" || e.pointerType === "pen" || e.pointerType === "virtual" || e.pointerType === "keyboard" && C && Dc(e.key) || e.pointerType === "mouse" && D.current) && (C ? k(e) : v && p(e));
	});
	let ee = ts(n.collection);
	if (m["data-collection"] = ee, m["data-key"] = r, A.preventFocusOnPress = o, o && (A = H(A, {
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
	]) O[e] && (A[e] = ar(A[e], O[e]));
	let { pressProps: j, isPressed: te } = pa(A), M = S ? (e) => {
		w.current === "mouse" && (e.stopPropagation(), e.preventDefault(), k(e));
	} : void 0, { longPressProps: ne } = Bs({
		isDisabled: !T,
		onLongPress(e) {
			e.pointerType === "touch" && (p(e), n.setSelectionBehavior("toggle"));
		}
	}), N = (e) => {
		w.current === "touch" && E.current && e.preventDefault();
	}, re = d !== "none" && n.isLink(r) ? (e) => {
		hn.isOpening || e.preventDefault();
	} : void 0, P = H(m, v || b || o && !c ? j : {}, T ? ne : {}, {
		onDoubleClick: M,
		onDragStartCapture: N,
		onClick: re,
		id: t
	}, o ? { onMouseDown: (e) => e.preventDefault() } : void 0), ie = (e) => {
		let t = e;
		for (; t && t !== i.current;) {
			let e = t.getAttribute("data-collection");
			if (e != null) return e !== ee;
			t = t.parentElement;
		}
		return Gt(e);
	}, ae = P.onPointerDown;
	P.onPointerDown = (e) => {
		let t = z(e);
		if (t && t !== i.current && ie(t)) {
			e.stopPropagation();
			return;
		}
		ae?.(e);
	};
	let oe = P.onMouseDown;
	return P.onMouseDown = (e) => {
		let t = z(e);
		if (t && t !== i.current && ie(t)) {
			e.stopPropagation();
			return;
		}
		oe?.(e);
	}, {
		itemProps: P,
		isPressed: te,
		isSelected: n.isSelected(r),
		isFocused: n.isFocused && n.focusedKey === r,
		isDisabled: c,
		allowsSelection: v,
		hasAction: C
	};
}
function Dc(e) {
	return e === "Enter";
}
function Oc(e) {
	return e === " ";
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/useListBox.mjs
function kc(e, t, n) {
	let r = U(e, { labelable: !0 }), i = e.selectionBehavior || "toggle", a = e.orientation || "vertical", o = e.linkBehavior || (i === "replace" ? "action" : "override");
	i === "toggle" && o === "action" && (o = "override");
	let { listProps: s } = Tc({
		...e,
		ref: n,
		selectionManager: t.selectionManager,
		collection: t.collection,
		disabledKeys: t.disabledKeys,
		linkBehavior: o
	}), { focusWithinProps: c } = No({
		onFocusWithin: e.onFocus,
		onBlurWithin: e.onBlur,
		onFocusWithinChange: e.onFocusChange
	}), l = dr(e.id);
	Jo.set(t, {
		id: l,
		shouldUseVirtualFocus: e.shouldUseVirtualFocus,
		shouldSelectOnPressUp: e.shouldSelectOnPressUp,
		shouldFocusOnHover: e.shouldFocusOnHover,
		isVirtualized: e.isVirtualized,
		onAction: e.onAction,
		linkBehavior: o,
		UNSTABLE_itemBehavior: e.UNSTABLE_itemBehavior
	});
	let { labelProps: u, fieldProps: d } = jo({
		...e,
		id: l,
		labelElementType: "span"
	});
	return {
		labelProps: u,
		listBoxProps: H(r, c, t.selectionManager.selectionMode === "multiple" ? { "aria-multiselectable": "true" } : {}, {
			role: "listbox",
			"aria-orientation": a,
			...H(d, s)
		})
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/listbox/useListBoxSection.mjs
function Ac(e) {
	let { heading: t, "aria-label": n } = e, r = dr();
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
function jc(e, t, n) {
	let { key: r } = e, i = Jo.get(t), a = e.isDisabled ?? t.selectionManager.isDisabled(r), o = e.isSelected ?? t.selectionManager.isSelected(r), s = e.shouldSelectOnPressUp ?? i?.shouldSelectOnPressUp, c = e.shouldFocusOnHover ?? i?.shouldFocusOnHover, l = e.shouldUseVirtualFocus ?? i?.shouldUseVirtualFocus, u = e.isVirtualized ?? i?.isVirtualized, d = pr(), f = pr(), p = {
		role: "option",
		"aria-disabled": a || void 0,
		"aria-selected": t.selectionManager.selectionMode === "none" ? void 0 : o,
		"aria-label": e["aria-label"],
		"aria-labelledby": d,
		"aria-describedby": f
	}, m = t.collection.getItem(r);
	if (u) {
		let e = Number(m?.index);
		p["aria-posinset"] = Number.isNaN(e) ? void 0 : e + 1, p["aria-setsize"] = ic(t.collection);
	}
	let h = i?.onAction ? () => i?.onAction?.(r) : void 0, g = Xo(t, r), { itemProps: _, isPressed: v, isFocused: y, hasAction: b, allowsSelection: x } = Ec({
		selectionManager: t.selectionManager,
		key: r,
		ref: n,
		shouldSelectOnPressUp: s,
		allowsDifferentPressOrigin: s && c,
		isVirtualized: u,
		shouldUseVirtualFocus: l,
		isDisabled: a,
		onAction: h || m?.props?.onAction ? ar(m?.props?.onAction, h) : void 0,
		linkBehavior: i?.linkBehavior,
		UNSTABLE_itemBehavior: i?.UNSTABLE_itemBehavior,
		id: g
	}), { hoverProps: S } = Sc({
		isDisabled: a || !c,
		onHoverStart() {
			qn() || (t.selectionManager.setFocused(!0), t.selectionManager.setFocusedKey(r));
		}
	}), C = U(m?.props);
	delete C.id;
	let w = vn(m?.props);
	return {
		optionProps: {
			...p,
			...H(C, _, S, w),
			id: g
		},
		labelProps: { id: d },
		descriptionProps: { id: f },
		isFocused: y,
		isFocusVisible: y && t.selectionManager.isFocused && qn(),
		isSelected: o,
		isDisabled: a,
		isPressed: v,
		allowsSelection: x,
		hasAction: b
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/useResizeObserver.mjs
function Mc() {
	return window.ResizeObserver !== void 0;
}
function Nc(e) {
	let { ref: t, box: n, onResize: r } = e, i = yi(r);
	(0, x.useEffect)(() => {
		let e = t?.current;
		if (e) {
			if (Mc()) {
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
var Pc = {};
Pc = { dismiss: "تجاهل" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/bg-BG.mjs
var Fc = {};
Fc = { dismiss: "Отхвърляне" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/cs-CZ.mjs
var Ic = {};
Ic = { dismiss: "Odstranit" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/da-DK.mjs
var Lc = {};
Lc = { dismiss: "Luk" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/de-DE.mjs
var Rc = {};
Rc = { dismiss: "Schließen" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/el-GR.mjs
var zc = {};
zc = { dismiss: "Απόρριψη" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/en-US.mjs
var Bc = {};
Bc = { dismiss: "Dismiss" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/es-ES.mjs
var Vc = {};
Vc = { dismiss: "Descartar" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/et-EE.mjs
var Hc = {};
Hc = { dismiss: "Lõpeta" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/fi-FI.mjs
var Uc = {};
Uc = { dismiss: "Hylkää" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/fr-FR.mjs
var Wc = {};
Wc = { dismiss: "Rejeter" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/he-IL.mjs
var Gc = {};
Gc = { dismiss: "התעלם" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/hr-HR.mjs
var Kc = {};
Kc = { dismiss: "Odbaci" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/hu-HU.mjs
var qc = {};
qc = { dismiss: "Elutasítás" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/it-IT.mjs
var Jc = {};
Jc = { dismiss: "Ignora" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ja-JP.mjs
var Yc = {};
Yc = { dismiss: "閉じる" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ko-KR.mjs
var Xc = {};
Xc = { dismiss: "무시" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/lt-LT.mjs
var Zc = {};
Zc = { dismiss: "Atmesti" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/lv-LV.mjs
var Qc = {};
Qc = { dismiss: "Nerādīt" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/nb-NO.mjs
var $c = {};
$c = { dismiss: "Lukk" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/nl-NL.mjs
var el = {};
el = { dismiss: "Negeren" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/pl-PL.mjs
var tl = {};
tl = { dismiss: "Zignoruj" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/pt-BR.mjs
var nl = {};
nl = { dismiss: "Descartar" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/pt-PT.mjs
var rl = {};
rl = { dismiss: "Dispensar" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ro-RO.mjs
var il = {};
il = { dismiss: "Revocare" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/ru-RU.mjs
var al = {};
al = { dismiss: "Пропустить" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sk-SK.mjs
var ol = {};
ol = { dismiss: "Zrušiť" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sl-SI.mjs
var sl = {};
sl = { dismiss: "Opusti" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sr-SP.mjs
var cl = {};
cl = { dismiss: "Odbaci" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/sv-SE.mjs
var ll = {};
ll = { dismiss: "Avvisa" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/tr-TR.mjs
var ul = {};
ul = { dismiss: "Kapat" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/uk-UA.mjs
var dl = {};
dl = { dismiss: "Скасувати" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/zh-CN.mjs
var fl = {};
fl = { dismiss: "取消" };
//#endregion
//#region node_modules/react-aria/dist/private/intl/overlays/zh-TW.mjs
var pl = {};
pl = { dismiss: "關閉" };
//#endregion
//#region node_modules/react-aria/dist/private/overlays/intlStrings.mjs
var ml = {};
ml = {
	"ar-AE": Pc,
	"bg-BG": Fc,
	"cs-CZ": Ic,
	"da-DK": Lc,
	"de-DE": Rc,
	"el-GR": zc,
	"en-US": Bc,
	"es-ES": Vc,
	"et-EE": Hc,
	"fi-FI": Uc,
	"fr-FR": Wc,
	"he-IL": Gc,
	"hr-HR": Kc,
	"hu-HU": qc,
	"it-IT": Jc,
	"ja-JP": Yc,
	"ko-KR": Xc,
	"lt-LT": Zc,
	"lv-LV": Qc,
	"nb-NO": $c,
	"nl-NL": el,
	"pl-PL": tl,
	"pt-BR": nl,
	"pt-PT": rl,
	"ro-RO": il,
	"ru-RU": al,
	"sk-SK": ol,
	"sl-SI": sl,
	"sr-SP": cl,
	"sv-SE": ll,
	"tr-TR": ul,
	"uk-UA": dl,
	"zh-CN": fl,
	"zh-TW": pl
};
//#endregion
//#region node_modules/react-aria/dist/private/overlays/DismissButton.mjs
function hl(e) {
	return e && e.__esModule ? e.default : e;
}
function gl(e) {
	let { onDismiss: t, ...n } = e, r = xi(n, Ki(hl(ml), "@react-aria/overlays").format("dismiss")), i = () => {
		t && t();
	};
	return /*#__PURE__*/ x.createElement(Bo, null, /*#__PURE__*/ x.createElement("button", {
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
var _l = [];
function vl(e, t) {
	let { onClose: n, shouldCloseOnBlur: r, isOpen: i, isDismissable: a = !1, isKeyboardDismissDisabled: o = !1, shouldCloseOnInteractOutside: s } = e, c = (0, x.useRef)(void 0);
	(0, x.useEffect)(() => {
		if (i && !_l.includes(t)) return _l.push(t), () => {
			let e = _l.indexOf(t);
			e >= 0 && _l.splice(e, 1);
		};
	}, [i, t]);
	let l = () => {
		_l[_l.length - 1] === t && n && n();
	}, u = (e) => {
		let n = _l[_l.length - 1];
		c.current = n, (!s || s(z(e))) && n === t && e.stopPropagation();
	}, d = (e) => {
		(!s || s(z(e))) && (_l[_l.length - 1] === t && e.stopPropagation(), c.current === t && l()), c.current = void 0;
	}, { keyboardProps: f } = Mr({ shortcuts: { Escape: () => {
		if (!o) {
			l();
			return;
		}
		return !1;
	} } });
	Cc({
		ref: t,
		onInteractOutside: a && i ? d : void 0,
		onInteractOutsideStart: u
	});
	let { focusWithinProps: p } = No({
		isDisabled: !r,
		onBlurWithin: (e) => {
			!e.relatedTarget || Ia(e.relatedTarget) || (!s || s(e.relatedTarget)) && n?.();
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
var yl = typeof document < "u" && window.visualViewport, bl = 0, xl;
function Sl(e = {}) {
	let { isDisabled: t } = e;
	V(() => {
		if (!t) return bl++, bl === 1 && (xl = an() && sn() ? wl() : Cl()), () => {
			bl--, bl === 0 && xl();
		};
	}, [t]);
}
function Cl() {
	let e = window.innerWidth - document.documentElement.clientWidth;
	return ar(e > 0 && ("scrollbarGutter" in document.documentElement.style ? Mt(document.documentElement, "scrollbar-gutter", "stable") : Mt(document.documentElement, "padding-right", `${e}px`)), Mt(document.documentElement, "overflow", "hidden"));
}
function wl() {
	let e = Mt(document.documentElement, "overflow", "hidden"), t, n = !1, r = (e) => {
		let r = z(e);
		t = eo(r) ? r : to(r, !0), n = !1;
		let i = r.ownerDocument.defaultView.getSelection();
		i && !i.isCollapsed && i.containsNode(r, !0) && (n = !0), e.composedPath().some((e) => e instanceof HTMLInputElement && e.type === "range") && (n = !0), "selectionStart" in r && "selectionEnd" in r && r.selectionStart < r.selectionEnd && r.ownerDocument.activeElement === r && (n = !0);
	}, i = document.createElement("style"), a = aa();
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
		let t = z(e), n = e.relatedTarget;
		n && _i(n) ? (n.focus({ preventScroll: !0 }), Tl(n, _i(t))) : n || (t.parentElement?.closest("[tabindex]"))?.focus({ preventScroll: !0 });
	}, c = HTMLElement.prototype.focus;
	Reflect.defineProperty(HTMLElement.prototype, "focus", {
		configurable: !0,
		writable: !0,
		value: function(e) {
			let t = Ft(), n = t != null && _i(t);
			c.call(this, {
				...e,
				preventScroll: !0
			}), (!e || !e.preventScroll) && Tl(this, n);
		}
	});
	let l = ar(jt(document, "touchstart", r, {
		passive: !1,
		capture: !0
	}), jt(document, "touchmove", o, {
		passive: !1,
		capture: !0
	}), jt(document, "blur", s, !0));
	return () => {
		e(), l(), i.remove(), Reflect.defineProperty(HTMLElement.prototype, "focus", {
			configurable: !0,
			writable: !0,
			value: c
		});
	};
}
function Tl(e, t) {
	t || !yl ? El(e) : yl.addEventListener("resize", () => El(e), { once: !0 });
}
function El(e) {
	let t = document.scrollingElement || document.documentElement, n = e;
	for (; n && n !== t;) {
		let e = to(n);
		if (e !== document.documentElement && e !== document.body && e !== n) {
			let t = e.getBoundingClientRect(), r = n.getBoundingClientRect();
			if (r.top < t.top || r.bottom > t.top + n.clientHeight) {
				let n = t.bottom;
				yl && (n = Math.min(n, yl.offsetTop + yl.height));
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
//#region node_modules/react-aria/dist/private/overlays/useModalOverlay.mjs
function Dl(e, t, n) {
	let { overlayProps: r, underlayProps: i } = vl({
		...e,
		isOpen: t.isOpen,
		onClose: t.close
	}, n);
	return Sl({ isDisabled: !t.isOpen }), pc(), (0, x.useEffect)(() => {
		if (t.isOpen && n.current) return Ko([n.current], { shouldUseInert: !0 });
	}, [t.isOpen, n]), {
		modalProps: H(r),
		underlayProps: i
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/calculatePosition.mjs
var Ol = {
	top: "top",
	bottom: "top",
	left: "left",
	right: "left"
}, kl = {
	top: "bottom",
	bottom: "top",
	left: "right",
	right: "left"
}, Al = {
	top: "left",
	left: "top"
}, jl = {
	top: "height",
	left: "width"
}, Ml = {
	width: "totalWidth",
	height: "totalHeight"
}, Nl = {}, Pl = () => typeof document < "u" ? window.visualViewport : null;
function Fl(e, t) {
	let n = 0, r = 0, i = 0, a = 0, o = 0, s = 0, c = {}, l = (t?.scale ?? 1) > 1;
	if (e.tagName === "BODY" || e.tagName === "HTML") {
		let l = document.documentElement;
		i = l.clientWidth, a = l.clientHeight, n = t?.width ?? i, r = t?.height ?? a, c.top = l.scrollTop || e.scrollTop, c.left = l.scrollLeft || e.scrollLeft, t && (o = Math.max(0, t.pageTop - (c.top ?? 0)), s = Math.max(0, t.pageLeft - (c.left ?? 0)));
	} else ({width: n, height: r, top: o, left: s} = Kl(e, !1)), c.top = e.scrollTop, c.left = e.scrollLeft, i = n, a = r;
	return sn() && (e.tagName === "BODY" || e.tagName === "HTML") && l && (c.top = 0, c.left = 0, o = t?.pageTop ?? 0, s = t?.pageLeft ?? 0), {
		width: n,
		height: r,
		totalWidth: i,
		totalHeight: a,
		scroll: c,
		top: o,
		left: s
	};
}
function Il(e) {
	return {
		top: e.scrollTop,
		left: e.scrollLeft,
		width: e.scrollWidth,
		height: e.scrollHeight
	};
}
function Ll(e, t, n, r, i, a, o) {
	let s = i.scroll[e] ?? 0, c = r[jl[e]], l = o[e] + r.scroll[Ol[e]] + a, u = o[e] + r.scroll[Ol[e]] + c - a, d = t - s + r.scroll[Ol[e]] + o[e] - r[Ol[e]], f = t - s + n + r.scroll[Ol[e]] + o[e] - r[Ol[e]];
	return d < l ? l - d : f > u ? Math.max(u - f, l - d) : 0;
}
function Rl(e) {
	let t = window.getComputedStyle(e);
	return {
		top: parseInt(t.marginTop, 10) || 0,
		bottom: parseInt(t.marginBottom, 10) || 0,
		left: parseInt(t.marginLeft, 10) || 0,
		right: parseInt(t.marginRight, 10) || 0
	};
}
function zl(e) {
	if (Nl[e]) return Nl[e];
	let [t, n] = e.split(" "), r = Ol[t] || "right", i = Al[r];
	Ol[n] || (n = "center");
	let a = jl[r], o = jl[i];
	return Nl[e] = {
		placement: t,
		crossPlacement: n,
		axis: r,
		crossAxis: i,
		size: a,
		crossSize: o
	}, Nl[e];
}
function Bl(e, t, n, r, i, a, o, s, c, l, u) {
	let { placement: d, crossPlacement: f, axis: p, crossAxis: m, size: h, crossSize: g } = r, _ = {};
	_[m] = e[m] ?? 0, f === "center" ? _[m] += ((e[g] ?? 0) - (n[g] ?? 0)) / 2 : f !== m && (_[m] += (e[g] ?? 0) - (n[g] ?? 0)), _[m] += a;
	let v = e[m] - n[g] + c + l, y = e[m] + e[g] - c - l;
	if (_[m] = Lo(_[m], v, y), d === p) {
		let t = s ? u[h] : u[Ml[h]];
		_[kl[p]] = Math.floor(t - e[p] + i);
	} else _[p] = Math.floor(e[p] + e[h] + i);
	return _;
}
function Vl(e, t, n, r, i, a, o, s, c, l, u) {
	let d = (e.top == null ? c[Ml.height] - (e.bottom ?? 0) - o : e.top) - (c.scroll.top ?? 0), f = l ? n.top : 0, p = {
		top: Math.max(t.top + f, (u?.offsetTop ?? t.top) + f),
		bottom: Math.min(t.top + t.height + f, (u?.offsetTop ?? 0) + (u?.height ?? 0))
	};
	return s === "top" ? Math.max(0, d + o - p.top - ((i.top ?? 0) + (i.bottom ?? 0) + a)) : Math.max(0, p.bottom - d - ((i.top ?? 0) + (i.bottom ?? 0) + a));
}
function Hl(e, t, n, r, i, a, o, s) {
	let { placement: c, axis: l, size: u } = a;
	return c === l ? Math.max(0, n[l] - (o.scroll[l] ?? 0) - (e[l] + (s ? t[l] : 0)) - (r[l] ?? 0) - r[kl[l]] - i) : Math.max(0, e[u] + e[l] + (s ? t[l] : 0) - n[l] - n[u] + (o.scroll[l] ?? 0) - (r[l] ?? 0) - r[kl[l]] - i);
}
function Ul(e, t, n, r, i, a, o, s, c, l, u, d, f, p, m, h, g, _) {
	let v = zl(e), { size: y, crossAxis: b, crossSize: x, placement: S, crossPlacement: C } = v, w = Bl(t, s, n, v, u, d, l, f, m, h, c), T = u, E = Hl(s, l, t, i, a + u, v, c, g);
	if (o && n[y] > E) {
		let e = zl(`${kl[S]} ${C}`), r = Bl(t, s, n, e, u, d, l, f, m, h, c);
		Hl(s, l, t, i, a + u, e, c, g) > E && (v = e, w = r, T = u);
	}
	let D = "bottom";
	v.axis === "top" ? v.placement === "top" ? D = "top" : v.placement === "bottom" && (D = "bottom") : v.crossAxis === "top" && (v.crossPlacement === "top" ? D = "bottom" : v.crossPlacement === "bottom" && (D = "top"));
	let O = Ll(b, w[b], n[x], s, c, a, l);
	w[b] += O;
	let k = Vl(w, s, l, f, i, a, n.height, D, c, g, _);
	p && p < k && (k = p), n.height = Math.min(n.height, k), w = Bl(t, s, n, v, T, d, l, f, m, h, c), O = Ll(b, w[b], n[x], s, c, a, l), w[b] += O;
	let A = {}, ee = t[b] - w[b] - i[Ol[b]], j = ee + .5 * t[x], te = m / 2 + h, M = Ol[b] === "left" ? (i.left ?? 0) + (i.right ?? 0) : (i.top ?? 0) + (i.bottom ?? 0), ne = n[x] - M - m / 2 - h;
	A[b] = Lo(Lo(j, t[b] + m / 2 - (w[b] + i[Ol[b]]), t[b] + t[x] - m / 2 - (w[b] + i[Ol[b]])), te, ne), {placement: S, crossPlacement: C} = v, m ? ee = A[b] : C === "right" ? ee += t[x] : C === "center" && (ee += t[x] / 2);
	let N = S === "left" || S === "top" ? n[y] : 0, re = {
		x: S === "top" || S === "bottom" ? ee : N,
		y: S === "left" || S === "right" ? ee : N
	};
	return {
		position: w,
		maxHeight: k,
		arrowOffsetLeft: A.left,
		arrowOffsetTop: A.top,
		placement: S,
		triggerAnchorPoint: re
	};
}
function Wl(e) {
	let { placement: t, targetNode: n, overlayNode: r, scrollNode: i, padding: a, shouldFlip: o, boundaryElement: s, offset: c, crossOffset: l, maxHeight: u, arrowSize: d = 0, arrowBoundaryOffset: f = 0, targetRect: p } = e, m = Pl(), h = r instanceof HTMLElement ? Jl(r) : document.documentElement, g = h === document.documentElement, _ = window.getComputedStyle(h).position, v = !!_ && _ !== "static", y = g ? Kl(n, !1, p) : ql(n, h, !1, p);
	if (!g) {
		let { marginTop: e, marginLeft: t } = window.getComputedStyle(n);
		y.top += parseInt(e, 10) || 0, y.left += parseInt(t, 10) || 0;
	}
	let b = Kl(r, !0), x = Rl(r);
	b.width += (x.left ?? 0) + (x.right ?? 0), b.height += (x.top ?? 0) + (x.bottom ?? 0);
	let S = Il(i), C = Fl(s, m), w = Fl(h, m), T;
	if ((s.tagName === "BODY" || s.tagName === "HTML") && !g) {
		let e = Gl(h, !1);
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
	} : ql(s, h, !1);
	let E = R(s, h);
	return Ul(t, y, b, S, x, a, o, C, w, T, c, l, v, u, d, f, E, m);
}
function Gl(e, t) {
	let { top: n, left: r, width: i, height: a } = e.getBoundingClientRect();
	return t && e instanceof e.ownerDocument.defaultView.HTMLElement && (i = e.offsetWidth, a = e.offsetHeight), {
		top: n,
		left: r,
		width: i,
		height: a
	};
}
function Kl(e, t, n) {
	let { top: r, left: i, width: a, height: o } = n || Gl(e, t), { scrollTop: s, scrollLeft: c, clientTop: l, clientLeft: u } = document.documentElement;
	return {
		top: r + s - l,
		left: i + c - u,
		width: a,
		height: o
	};
}
function ql(e, t, n, r) {
	let i = window.getComputedStyle(e), a;
	if (i.position === "fixed") a = r || Gl(e, n);
	else {
		a = Kl(e, n, r);
		let i = Kl(t, n), o = window.getComputedStyle(t);
		i.top += (parseInt(o.borderTopWidth, 10) || 0) - t.scrollTop, i.left += (parseInt(o.borderLeftWidth, 10) || 0) - t.scrollLeft, a.top -= i.top, a.left -= i.left;
	}
	return a.top -= parseInt(i.marginTop, 10) || 0, a.left -= parseInt(i.marginLeft, 10) || 0, a;
}
function Jl(e) {
	let t = e.offsetParent;
	if (t && t === document.body && window.getComputedStyle(t).position === "static" && !Yl(t) && (t = document.documentElement), t == null) for (t = e.parentElement; t && !Yl(t);) t = t.parentElement;
	return t || document.documentElement;
}
function Yl(e) {
	let t = window.getComputedStyle(e);
	return t.transform !== "none" || /transform|perspective/.test(t.willChange) || t.filter !== "none" || t.contain === "paint" || "backdropFilter" in t && t.backdropFilter !== "none" || "WebkitBackdropFilter" in t && t.WebkitBackdropFilter !== "none";
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/useOverlayPosition.mjs
var Xl = typeof document < "u" ? window.visualViewport : null;
function Zl(e) {
	let { direction: t } = Mi(), { arrowSize: n, targetRef: r, overlayRef: i, arrowRef: a, scrollRef: o = i, placement: s = "bottom", containerPadding: c = 12, shouldFlip: l = !0, boundaryElement: u = typeof document < "u" ? document.body : null, offset: d = 0, crossOffset: f = 0, shouldUpdatePosition: p = !0, isOpen: m = !0, onClose: h, maxHeight: g, arrowBoundaryOffset: _ = 0, getTargetRect: v } = e, [y, b] = (0, x.useState)(null), S = [
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
	], C = (0, x.useRef)(Xl?.scale);
	(0, x.useEffect)(() => {
		m && (C.current = Xl?.scale);
	}, [m]);
	let w = (0, x.useCallback)(() => {
		if (p === !1 || !m || !i.current || !r.current || !u || Xl?.scale !== C.current) return;
		let e = null;
		if (o.current && Lt(o.current)) {
			let t = Ft()?.getBoundingClientRect(), n = o.current.getBoundingClientRect();
			e = {
				type: "top",
				offset: (t?.top ?? 0) - n.top
			}, e.offset > n.height / 2 && (e.type = "bottom", e.offset = (t?.bottom ?? 0) - n.bottom);
		}
		let h = i.current;
		!g && i.current && (h.style.top = "0px", h.style.bottom = "", h.style.maxHeight = (window.visualViewport?.height ?? window.innerHeight) + "px");
		let y = Wl({
			placement: $l(s, t),
			overlayNode: i.current,
			targetNode: r.current,
			scrollNode: o.current || i.current,
			padding: c,
			shouldFlip: l,
			boundaryElement: u,
			offset: d,
			crossOffset: f,
			maxHeight: g,
			arrowSize: n ?? (a?.current ? Gl(a.current, !0).width : 0),
			arrowBoundaryOffset: _,
			targetRect: v?.(r.current)
		});
		if (!y.position) return;
		h.style.top = "", h.style.bottom = "", h.style.left = "", h.style.right = "", Object.keys(y.position).forEach((e) => h.style[e] = y.position[e] + "px"), h.style.maxHeight = y.maxHeight == null ? "" : y.maxHeight + "px";
		let x = Ft();
		if (e && x && o.current) {
			let t = x.getBoundingClientRect(), n = o.current.getBoundingClientRect(), r = t[e.type] - n[e.type];
			o.current.scrollTop += r - e.offset;
		}
		b(y);
	}, S);
	V(w, S), Ql(w), Nc({
		ref: i,
		onResize: w
	}), Nc({
		ref: r,
		onResize: w
	});
	let T = (0, x.useRef)(!1);
	V(() => {
		let e, t = () => {
			T.current = !0, clearTimeout(e), e = setTimeout(() => {
				T.current = !1;
			}, 500), w();
		}, n = () => {
			T.current && t();
		};
		Xl?.addEventListener("resize", t), Xl?.addEventListener("scroll", n);
		let r = jt(It(window), "scroll", n);
		return () => {
			Xl?.removeEventListener("resize", t), Xl?.removeEventListener("scroll", n), r();
		};
	}, [w]);
	let E = (0, x.useCallback)(() => {
		T.current || h?.();
	}, [h, T]);
	return Us({
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
function Ql(e) {
	V(() => (window.addEventListener("resize", e, !1), () => {
		window.removeEventListener("resize", e, !1);
	}), [e]);
}
function $l(e, t) {
	return t === "rtl" ? e.replace("start", "right").replace("end", "left") : e.replace("start", "left").replace("end", "right");
}
//#endregion
//#region node_modules/react-aria/dist/private/overlays/usePopover.mjs
function eu(e, t) {
	let { triggerRef: n, popoverRef: r, groupRef: i, isNonModal: a, isKeyboardDismissDisabled: o, shouldCloseOnInteractOutside: s, ...c } = e, l = c.trigger === "SubmenuTrigger", { overlayProps: u, underlayProps: d } = vl({
		isOpen: t.isOpen,
		onClose: t.close,
		shouldCloseOnBlur: !0,
		isDismissable: !a || l,
		isKeyboardDismissDisabled: o,
		shouldCloseOnInteractOutside: s
	}, i ?? r), { overlayProps: f, arrowProps: p, placement: m, triggerAnchorPoint: h } = Zl({
		...c,
		targetRef: n,
		overlayRef: r,
		isOpen: t.isOpen,
		onClose: a && !l ? t.close : null,
		getTargetRect: c.getTargetRect ?? (t.point ? () => new DOMRect(t.point.x, t.point.y, 0, 0) : void 0)
	});
	Sl({ isDisabled: a || !t.isOpen }), (0, x.useEffect)(() => {
		if (t.isOpen && r.current) return a ? qo(i?.current ?? r.current) : Ko([i?.current ?? r.current], { shouldUseInert: !0 });
	}, [
		a,
		t.isOpen,
		r,
		i
	]);
	let { focusWithinProps: g } = No(e);
	return {
		popoverProps: H(u, f, g),
		arrowProps: p,
		underlayProps: d,
		placement: m,
		triggerAnchorPoint: h
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/radio/utils.mjs
var tu = /* @__PURE__ */ new WeakMap();
//#endregion
//#region node_modules/react-aria/dist/private/radio/useRadio.mjs
function nu(e, t, n) {
	let { value: r, children: i, "aria-label": a, "aria-labelledby": o, onPressStart: s, onPressEnd: c, onPressChange: l, onPress: u, onPressUp: d, onClick: f } = e, p = e.isDisabled || t.isDisabled, m = t.selectedValue === r, h = (e) => {
		e.stopPropagation(), t.setSelectedValue(r);
	}, { pressProps: g, isPressed: _ } = pa({
		onPressStart: s,
		onPressEnd: c,
		onPressChange: l,
		onPress: u,
		onPressUp: d,
		onClick: f,
		isDisabled: p
	}), { pressProps: v, isPressed: y } = pa({
		onPressStart: s,
		onPressEnd: c,
		onPressChange: l,
		onPressUp: d,
		onClick: f,
		isDisabled: p,
		onPress(e) {
			u?.(e), t.setSelectedValue(r), n.current?.focus();
		}
	}), { focusableProps: b } = Lr(H(e, { onFocus: () => t.setLastFocusedValue(r) }), n), S = H(g, b), C = U(e, { labelable: !0 }), w = -1;
	t.selectedValue == null ? (t.lastFocusedValue === r || t.lastFocusedValue == null) && (w = 0) : t.selectedValue === r && (w = 0), p && (w = void 0);
	let { name: T, form: E, descriptionId: D, errorMessageId: O, validationBehavior: k } = tu.get(t);
	lo(n, t.defaultSelectedValue, t.setSelectedValue), uo({ validationBehavior: k }, t, n);
	let A = go();
	return {
		labelProps: H(v, (0, x.useMemo)(() => ({
			onClick: (e) => e.preventDefault(),
			onMouseDown: (e) => e.preventDefault()
		}), [])),
		inputProps: H(C, {
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
function ru(e, t) {
	let { name: n, form: r, isReadOnly: i, isRequired: a, isDisabled: o, orientation: s = "vertical", validationBehavior: c = "aria" } = e, { direction: l } = Mi(), { isInvalid: u, validationErrors: d, validationDetails: f } = t.displayValidation, { labelProps: p, fieldProps: m, descriptionProps: h, errorMessageProps: g } = Mo({
		...e,
		labelElementType: "span",
		isInvalid: t.isInvalid,
		errorMessage: e.errorMessage || d
	}), _ = U(e, { labelable: !0 }), { focusWithinProps: v } = No({
		onBlurWithin(n) {
			e.onBlur?.(n), t.selectedValue || t.setLastFocusedValue(null);
		},
		onFocusWithin: e.onFocus,
		onFocusWithinChange: e.onFocusChange
	});
	function y(e, n) {
		let r = Ka(n.currentTarget, {
			from: z(n),
			accept: (e) => e instanceof Et(e).HTMLInputElement && e.type === "radio"
		}), i;
		return e === "next" ? (i = r.nextNode(), i ||= (r.currentNode = n.currentTarget, r.firstChild())) : (i = r.previousNode(), i ||= (r.currentNode = n.currentTarget, r.lastChild())), i ? (i.focus(), t.setSelectedValue(i.value), !0) : !1;
	}
	let { keyboardProps: b } = Mr({
		shortcuts: {
			ArrowRight: (e) => y(l === "rtl" && s !== "vertical" ? "prev" : "next", e),
			ArrowLeft: (e) => y(l === "rtl" && s !== "vertical" ? "next" : "prev", e),
			ArrowDown: (e) => y("next", e),
			ArrowUp: (e) => y("prev", e)
		},
		allowRepeats: !0
	}), x = dr(n);
	return tu.set(t, {
		name: x,
		form: r,
		descriptionId: h.id,
		errorMessageId: g.id,
		validationBehavior: c
	}), {
		radioGroupProps: H(_, {
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
var iu = /* @__PURE__ */ new WeakMap();
function au(e, t, n) {
	let { keyboardDelegate: r, isDisabled: i, isRequired: a, name: o, form: s, validationBehavior: c = "aria" } = e, l = oc({
		usage: "search",
		sensitivity: "base"
	}), u = (0, x.useMemo)(() => r || new rs(t.collection, t.disabledKeys, n, l), [
		r,
		t.collection,
		t.disabledKeys,
		l,
		n
	]), { menuTriggerProps: d, menuProps: f } = Ks({
		isDisabled: i,
		type: "listbox"
	}, t, n), { keyboardProps: p } = Mr({
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
	}), { typeSelectProps: m } = Js({
		keyboardDelegate: u,
		selectionManager: t.selectionManager,
		onTypeSelect(e) {
			t.setSelectedKey(e);
		}
	}), { isInvalid: h, validationErrors: g, validationDetails: _ } = t.displayValidation, { labelProps: v, fieldProps: y, descriptionProps: b, errorMessageProps: S } = Mo({
		...e,
		labelElementType: "span",
		isInvalid: h,
		errorMessage: e.errorMessage || g
	});
	t.selectionManager.selectionMode === "multiple" && (m = {});
	let C = U(e, { labelable: !0 }), w = H(m, d, y), T = dr();
	return iu.set(t, {
		isDisabled: i,
		isRequired: a,
		name: o,
		form: s,
		validationBehavior: c
	}), {
		labelProps: {
			...v,
			onClick: () => {
				e.isDisabled || (n.current?.focus(), Yn("keyboard"));
			}
		},
		triggerProps: H(C, {
			...w,
			isDisabled: i,
			onKeyDown: ar(w.onKeyDown, p.onKeyDown),
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
				R(n.currentTarget, n.relatedTarget) || (e.onBlur && e.onBlur(n), e.onFocusChange && e.onFocusChange(!1), t.setFocused(!1));
			},
			"aria-labelledby": [y["aria-labelledby"], w["aria-label"] && !y["aria-labelledby"] ? w.id : null].filter(Boolean).join(" ")
		},
		descriptionProps: b,
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
function ou(e, t, n) {
	let r = iu.get(t) || {}, { autoComplete: i, name: a = r.name, form: o = r.form, isDisabled: s = r.isDisabled } = e, { validationBehavior: c, isRequired: l } = r, { visuallyHiddenProps: u } = zo({ style: {
		position: "fixed",
		top: 0,
		left: 0
	} });
	lo(e.selectRef, t.defaultValue, t.setValue), uo({
		validationBehavior: c,
		focus: () => n.current?.focus()
	}, t, e.selectRef);
	let d = t.setValue, f = (0, x.useCallback)((e) => {
		let t = z(e);
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
function su(e) {
	let { state: t, triggerRef: n, label: r, name: i, form: a, isDisabled: o } = e, s = (0, x.useRef)(null), c = (0, x.useRef)(null), { containerProps: l, selectProps: u } = ou({
		...e,
		selectRef: t.collection.size <= 300 ? s : c
	}, t, n), d = Array.isArray(t.value) ? t.value : [t.value];
	if (t.collection.size <= 300) return /*#__PURE__*/ x.createElement("div", {
		...l,
		"data-testid": "hidden-select-container"
	}, /*#__PURE__*/ x.createElement("label", null, r, /*#__PURE__*/ x.createElement("select", {
		...u,
		ref: s
	}, /*#__PURE__*/ x.createElement("option", {
		value: "",
		label: "\xA0"
	}, "\xA0"), [...t.collection.getKeys()].map((e) => {
		let n = t.collection.getItem(e);
		if (n && n.type === "item") return /*#__PURE__*/ x.createElement("option", {
			key: n.key,
			value: n.key
		}, n.textValue);
	}), t.collection.size === 0 && i && d.map((e, t) => /*#__PURE__*/ x.createElement("option", {
		key: t,
		value: e ?? ""
	})))));
	if (i) {
		let { validationBehavior: e } = iu.get(t) || {};
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
			return e === "native" ? /*#__PURE__*/ x.createElement("input", {
				key: n,
				...r,
				ref: n === 0 ? c : null,
				style: { display: "none" },
				type: "text",
				required: n === 0 && u.required,
				onChange: () => {}
			}) : /*#__PURE__*/ x.createElement("input", {
				key: n,
				...r,
				ref: n === 0 ? c : null
			});
		});
		return /*#__PURE__*/ x.createElement(x.Fragment, null, n);
	}
	return null;
}
//#endregion
//#region node_modules/react-aria/dist/private/switch/useSwitch.mjs
function cu(e, t, n) {
	let { labelProps: r, inputProps: i, isSelected: a, ...o } = Oo(e, t, n);
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
var lu = /* @__PURE__ */ m(((e) => {
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
				t !== null && ee(x, t.startTime - e);
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
								u !== null && ee(x, u.startTime - t), i = !1;
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
	function ee(t, n) {
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
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (v(C), C = -1) : h = !0, ee(x, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, S || (S = !0, O()))), r;
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
})), uu = /* @__PURE__ */ m(((e, t) => {
	t.exports = lu();
})), du = /* @__PURE__ */ m(((e) => {
	var t = uu(), n = v(), r = Ur();
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
	function _(e) {
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
	var T = Object.assign, E = Symbol.for("react.element"), D = Symbol.for("react.transitional.element"), O = Symbol.for("react.portal"), k = Symbol.for("react.fragment"), A = Symbol.for("react.strict_mode"), ee = Symbol.for("react.profiler"), j = Symbol.for("react.consumer"), te = Symbol.for("react.context"), M = Symbol.for("react.forward_ref"), ne = Symbol.for("react.suspense"), N = Symbol.for("react.suspense_list"), re = Symbol.for("react.memo"), P = Symbol.for("react.lazy"), ie = Symbol.for("react.activity"), ae = Symbol.for("react.legacy_hidden"), oe = Symbol.for("react.memo_cache_sentinel"), se = Symbol.for("react.view_transition"), ce = Symbol.for("react.recoverable"), le = Symbol.iterator;
	function ue(e) {
		return typeof e != "object" || !e ? null : (e = le && e[le] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var de = Symbol.for("react.client.reference");
	function fe(e) {
		if (e == null) return null;
		if (typeof e == "function") return e.$$typeof === de ? null : e.displayName || e.name || null;
		if (typeof e == "string") return e;
		switch (e) {
			case k: return "Fragment";
			case ee: return "Profiler";
			case A: return "StrictMode";
			case ne: return "Suspense";
			case N: return "SuspenseList";
			case ie: return "Activity";
			case se: return "ViewTransition";
		}
		if (typeof e == "object") switch (e.$$typeof) {
			case O: return "Portal";
			case te: return e.displayName || "Context";
			case j: return (e._context.displayName || "Context") + ".Consumer";
			case M:
				var t = e.render;
				return e = e.displayName, e ||= (e = t.displayName || t.name || "", e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
			case re: return t = e.displayName || null, t === null ? fe(e.type) || "Memo" : t;
			case P:
				t = e._payload, e = e._init;
				try {
					return fe(e(t));
				} catch {}
		}
		return null;
	}
	var pe = Array.isArray, F = n.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, I = r.__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, me = {
		pending: !1,
		data: null,
		method: null,
		action: null
	}, he = [], ge = -1;
	function _e(e) {
		return { current: e };
	}
	function ve(e) {
		0 > ge || (e.current = he[ge], he[ge] = null, ge--);
	}
	function ye(e, t) {
		ge++, he[ge] = e.current, e.current = t;
	}
	var be = _e(null), xe = _e(null), Se = _e(null), Ce = _e(null);
	function we(e, t) {
		switch (ye(Se, t), ye(xe, e), ye(be, null), t.nodeType) {
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
		ve(be), ye(be, e);
	}
	function Te() {
		ve(be), ve(xe), ve(Se);
	}
	function Ee(e) {
		var t = e.memoizedState;
		t !== null && (sh._currentValue = t.memoizedState, ye(Ce, e)), t = be.current;
		var n = dp(t, e.type);
		t !== n && (ye(xe, e), ye(be, n));
	}
	function De(e) {
		xe.current === e && (ve(be), ve(xe)), Ce.current === e && (ve(Ce), sh._currentValue = me);
	}
	var Oe, ke;
	function Ae(e) {
		if (Oe === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			Oe = t && t[1] || "", ke = -1 < e.stack.indexOf("\n    at") ? " (<anonymous>)" : -1 < e.stack.indexOf("@") ? "@unknown:0:0" : "";
		}
		return "\n" + Oe + e + ke;
	}
	var je = !1;
	function Me(e, t) {
		if (!e || je) return "";
		je = !0;
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
			je = !1, Error.prepareStackTrace = n;
		}
		return (n = e ? e.displayName || e.name : "") ? Ae(n) : "";
	}
	function Ne(e, t) {
		switch (e.tag) {
			case 26:
			case 27:
			case 5: return Ae(e.type);
			case 16: return Ae("Lazy");
			case 13: return e.child !== t && t !== null ? Ae("Suspense Fallback") : Ae("Suspense");
			case 19: return Ae("SuspenseList");
			case 0:
			case 15: return Me(e.type, !1);
			case 11: return Me(e.type.render, !1);
			case 1: return Me(e.type, !0);
			case 31: return Ae("Activity");
			case 30: return Ae("ViewTransition");
			default: return "";
		}
	}
	function Pe(e) {
		try {
			var t = "", n = null;
			do
				t += Ne(e, n), n = e, e = e.return;
			while (e);
			return t;
		} catch (e) {
			return "\nError generating stack: " + e.message + "\n" + e.stack;
		}
	}
	var Fe = Object.prototype.hasOwnProperty, Ie = t.unstable_scheduleCallback, Le = t.unstable_cancelCallback, Re = t.unstable_shouldYield, ze = t.unstable_requestPaint, Be = t.unstable_now, Ve = t.unstable_getCurrentPriorityLevel, He = t.unstable_ImmediatePriority, Ue = t.unstable_UserBlockingPriority, We = t.unstable_NormalPriority, Ge = t.unstable_LowPriority, Ke = t.unstable_IdlePriority, qe = t.log, Je = t.unstable_setDisableYieldValue, Ye = null, Xe = null;
	function Ze(e) {
		if (typeof qe == "function" && Je(e), Xe && typeof Xe.setStrictMode == "function") try {
			Xe.setStrictMode(Ye, e);
		} catch {}
	}
	var Qe = Math.clz32 ? Math.clz32 : tt, $e = Math.log, et = Math.LN2;
	function tt(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - ($e(e) / et | 0) | 0;
	}
	var nt = 256, rt = 262144, it = 4194304;
	function at(e) {
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
	function ot(e, t, n) {
		var r = e.pendingLanes;
		if (r === 0) return 0;
		var i = 0, a = e.suspendedLanes, o = e.pingedLanes;
		e = e.warmLanes;
		var s = r & 134217727;
		return s === 0 ? (s = r & ~a, s === 0 ? o === 0 ? n || (n = r & ~e, n !== 0 && (i = at(n))) : i = at(o) : i = at(s)) : (r = s & ~a, r === 0 ? (o &= s, o === 0 ? n || (n = s & ~e, n !== 0 && (i = at(n))) : i = at(o)) : i = at(r)), i === 0 ? 0 : t !== 0 && t !== i && (t & a) === 0 && (a = i & -i, n = t & -t, a >= n || a === 32 && n & 4194048) ? t : i;
	}
	function st(e, t) {
		return (e.pendingLanes & ~(e.suspendedLanes & ~e.pingedLanes) & t) === 0;
	}
	function ct(e, t) {
		t & 8 && (t |= t & 32);
		var n = e.entangledLanes;
		if (n !== 0) for (e = e.entanglements, n &= t; 0 < n;) {
			var r = 31 - Qe(n), i = 1 << r;
			t |= e[r], n &= ~i;
		}
		return t;
	}
	function lt(e, t) {
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
	function ut() {
		var e = it;
		return it <<= 1, !(it & 62914560) && (it = 4194304), e;
	}
	function dt(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function ft(e, t) {
		e.pendingLanes |= t, t !== 268435456 && (e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0);
	}
	function pt(e, t, n, r, i, a) {
		var o = e.pendingLanes;
		e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.warmLanes = 0, e.expiredLanes &= n, e.entangledLanes &= n, e.errorRecoveryDisabledLanes &= n, e.shellSuspendCounter = 0;
		var s = e.entanglements, c = e.expirationTimes, l = e.hiddenUpdates;
		for (n = o & ~n; 0 < n;) {
			var u = 31 - Qe(n), d = 1 << u;
			s[u] = 0, c[u] = -1;
			var f = l[u];
			if (f !== null) for (l[u] = null, u = 0; u < f.length; u++) {
				var p = f[u];
				p !== null && (p.lane &= -536870913);
			}
			n &= ~d;
		}
		r !== 0 && mt(e, r, 0), a !== 0 && i === 0 && e.tag !== 0 && (e.suspendedLanes |= a & ~(o & ~t));
	}
	function mt(e, t, n) {
		e.pendingLanes |= t, e.suspendedLanes &= ~t;
		var r = 31 - Qe(t);
		e.entangledLanes |= t, e.entanglements[r] = e.entanglements[r] | 1073741824 | n & 261930;
	}
	function ht(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - Qe(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	function gt(e, t) {
		var n = t & -t;
		return n = n & 42 ? 1 : _t(n), (n & (e.suspendedLanes | t)) === 0 ? n : 0;
	}
	function _t(e) {
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
	function vt(e) {
		return e &= -e, 2 < e ? 8 < e ? e & 134217727 ? 32 : 268435456 : 8 : 2;
	}
	function yt() {
		var e = I.p;
		return e === 0 ? (e = window.event, e === void 0 ? 32 : Ch(e.type)) : e;
	}
	function bt(e, t) {
		var n = I.p;
		try {
			return I.p = e, t();
		} finally {
			I.p = n;
		}
	}
	var xt = Math.random().toString(36).slice(2), St = "__reactFiber$" + xt, Ct = "__reactProps$" + xt, wt = "__reactContainer$" + xt, Tt = "__reactEvents$" + xt, L = "__reactListeners$" + xt, Et = "__reactHandles$" + xt, Dt = "__reactResources$" + xt, Ot = "__reactMarker$" + xt, kt = "__reactLoad$" + xt;
	function At(e) {
		delete e[St], delete e[Ct], delete e[L], delete e[Et];
	}
	function jt(e) {
		var t;
		if (t = e[St]) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[wt] || n[St]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = fm(e); e !== null;) {
					if (n = e[St]) return n;
					e = fm(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function Mt(e) {
		if (e = e[St] || e[wt]) {
			var t = e.tag;
			if (t === 5 || t === 6 || t === 13 || t === 31 || t === 26 || t === 27 || t === 3) return e;
		}
		return null;
	}
	function Nt(e) {
		var t = e.tag;
		if (t === 5 || t === 26 || t === 27 || t === 6) return e.stateNode;
		throw Error(i(33));
	}
	function Pt(e) {
		var t = e[Dt];
		return t ||= e[Dt] = {
			hoistableStyles: /* @__PURE__ */ new Map(),
			hoistableScripts: /* @__PURE__ */ new Map()
		}, t;
	}
	function R(e) {
		e[Ot] = !0;
	}
	function Ft(e) {
		e[kt] = void 0;
	}
	var z = /* @__PURE__ */ new Set(), It = {};
	function Lt(e, t) {
		Rt(e, t), Rt(e + "Capture", t);
	}
	function Rt(e, t) {
		for (It[e] = t, e = 0; e < t.length; e++) z.add(t[e]);
	}
	var zt = RegExp("^[:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][:A-Z_a-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$"), Bt = {}, Vt = {};
	function Ht(e) {
		return Fe.call(Vt, e) ? !0 : Fe.call(Bt, e) ? !1 : zt.test(e) ? Vt[e] = !0 : (Bt[e] = !0, !1);
	}
	var B = !1;
	function Ut() {
		var e = B;
		return B = !1, e;
	}
	function Wt(e, t, n) {
		if (Ht(t)) {
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
	function Gt(e, t, n) {
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
	function Kt(e, t, n, r) {
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
	function V(e) {
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
	function qt(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function Jt(e, t, n) {
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
	function Yt(e) {
		if (!e._valueTracker) {
			var t = qt(e) ? "checked" : "value";
			e._valueTracker = Jt(e, t, "" + e[t]);
		}
	}
	function Xt(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = qt(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== n && (t.setValue(e), !0);
	}
	var Zt = /[\n"\\]/g;
	function Qt(e) {
		return e.replace(Zt, function(e) {
			return "\\" + e.charCodeAt(0).toString(16) + " ";
		});
	}
	function $t(e, t, n, r, i, a, o, s) {
		e.name = "", o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" ? e.type = o : e.removeAttribute("type"), t == null ? o !== "submit" && o !== "reset" || e.removeAttribute("value") : o === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + V(t)) : e.value !== "" + V(t) && (e.value = "" + V(t)), t == null ? n == null ? r != null && e.removeAttribute("value") : tn(e, V(n)) : o === "number" && e.value == t ? tn(e, V(e.value)) : tn(e, V(t)), i == null && a != null && (e.defaultChecked = !!a), i != null && (e.checked = i && typeof i != "function" && typeof i != "symbol"), s != null && typeof s != "function" && typeof s != "symbol" && typeof s != "boolean" ? e.name = "" + V(s) : e.removeAttribute("name");
	}
	function en(e, t, n, r, i, a, o, s) {
		if (a != null && typeof a != "function" && typeof a != "symbol" && typeof a != "boolean" && (e.type = a), t != null || n != null) {
			if (!(a !== "submit" && a !== "reset" || t != null)) {
				Yt(e);
				return;
			}
			n = n == null ? "" : "" + V(n), t = t == null ? n : "" + V(t), s || t === e.value || (e.value = t), e.defaultValue = t;
		}
		r ??= i, r = typeof r != "function" && typeof r != "symbol" && !!r, e.checked = s ? e.checked : !!r, e.defaultChecked = !!r, o != null && typeof o != "function" && typeof o != "symbol" && typeof o != "boolean" && (e.name = o), Yt(e);
	}
	function tn(e, t) {
		e.defaultValue !== "" + t && (e.defaultValue = "" + t);
	}
	function nn(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + V(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function rn(e, t, n) {
		if (t != null && (t = "" + V(t), t !== e.value && (e.value = t), n == null)) {
			e.defaultValue !== t && (e.defaultValue = t);
			return;
		}
		e.defaultValue = n == null ? "" : "" + V(n);
	}
	function an(e, t, n, r) {
		if (t == null) {
			if (r != null) {
				if (n != null) throw Error(i(92));
				if (pe(r)) {
					if (1 < r.length) throw Error(i(93));
					r = r[0];
				}
				n = r;
			}
			n ??= "", t = n;
		}
		n = V(t), e.defaultValue = n, r = e.textContent, r === n && r !== "" && r !== null && (e.value = r), Yt(e);
	}
	function on(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var sn = new Set("animationIterationCount aspectRatio borderImageOutset borderImageSlice borderImageWidth boxFlex boxFlexGroup boxOrdinalGroup columnCount columns flex flexGrow flexPositive flexShrink flexNegative flexOrder gridArea gridRow gridRowEnd gridRowSpan gridRowStart gridColumn gridColumnEnd gridColumnSpan gridColumnStart fontWeight lineClamp lineHeight opacity order orphans scale tabSize widows zIndex zoom fillOpacity floodOpacity stopOpacity strokeDasharray strokeDashoffset strokeMiterlimit strokeOpacity strokeWidth MozAnimationIterationCount MozBoxFlex MozBoxFlexGroup MozLineClamp msAnimationIterationCount msFlex msZoom msFlexGrow msFlexNegative msFlexOrder msFlexPositive msFlexShrink msGridColumn msGridColumnSpan msGridRow msGridRowSpan WebkitAnimationIterationCount WebkitBoxFlex WebKitBoxFlexGroup WebkitBoxOrdinalGroup WebkitColumnCount WebkitColumns WebkitFlex WebkitFlexGrow WebkitFlexPositive WebkitFlexShrink WebkitLineClamp".split(" "));
	function cn(e, t, n) {
		var r = t.indexOf("--") === 0;
		n == null || typeof n == "boolean" || n === "" ? r ? e.setProperty(t, "") : t === "float" ? e.cssFloat = "" : e[t] = "" : r ? e.setProperty(t, n) : typeof n != "number" || n === 0 || sn.has(t) ? t === "float" ? e.cssFloat = n : e[t] = ("" + n).trim() : e[t] = n + "px";
	}
	function ln(e, t, n) {
		if (t != null && typeof t != "object") throw Error(i(62));
		if (e = e.style, n != null) {
			for (var r in n) !n.hasOwnProperty(r) || t != null && t.hasOwnProperty(r) || (r.indexOf("--") === 0 ? e.setProperty(r, "") : r === "float" ? e.cssFloat = "" : e[r] = "", B = !0);
			for (var a in t) r = t[a], t.hasOwnProperty(a) && n[a] !== r && (cn(e, a, r), B = !0);
		} else for (var o in t) t.hasOwnProperty(o) && cn(e, o, t[o]);
	}
	function un(e) {
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
	var dn = /* @__PURE__ */ new Map([
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
	]), fn = /^[\u0000-\u001F ]*j[\r\n\t]*a[\r\n\t]*v[\r\n\t]*a[\r\n\t]*s[\r\n\t]*c[\r\n\t]*r[\r\n\t]*i[\r\n\t]*p[\r\n\t]*t[\r\n\t]*:/i;
	function pn(e) {
		return fn.test("" + e) ? "javascript:throw new Error('React has blocked a javascript: URL as a security precaution.')" : e;
	}
	function mn() {}
	var hn = null;
	function gn(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var _n = null, vn = null;
	function yn(e) {
		var t = Mt(e);
		if (t && (e = t.stateNode)) {
			var n = e[Ct] || null;
			a: switch (e = t.stateNode, t.type) {
				case "input":
					if ($t(e, n.value, n.defaultValue, n.defaultValue, n.checked, n.defaultChecked, n.type, n.name), t = n.name, n.type === "radio" && t != null) {
						for (n = e; n.parentNode;) n = n.parentNode;
						for (n = n.querySelectorAll("input[name=\"" + Qt("" + t) + "\"][type=\"radio\"]"), t = 0; t < n.length; t++) {
							var r = n[t];
							if (r !== e && r.form === e.form) {
								var a = r[Ct] || null;
								if (!a) throw Error(i(90));
								$t(r, a.value, a.defaultValue, a.defaultValue, a.checked, a.defaultChecked, a.type, a.name);
							}
						}
						for (t = 0; t < n.length; t++) r = n[t], r.form === e.form && Xt(r);
					}
					break a;
				case "textarea":
					rn(e, n.value, n.defaultValue);
					break a;
				case "select": t = n.value, t != null && nn(e, !!n.multiple, t, !1);
			}
		}
	}
	var bn = !1;
	function xn(e, t, n) {
		if (bn) return e(t, n);
		bn = !0;
		try {
			return e(t);
		} finally {
			if (bn = !1, (_n !== null || vn !== null) && (Rd(), _n && (t = _n, e = vn, vn = _n = null, yn(t), e))) for (t = 0; t < e.length; t++) yn(e[t]);
		}
	}
	function Sn(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var r = n[Ct] || null;
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
	var Cn = !(typeof window > "u" || window.document === void 0 || window.document.createElement === void 0), wn = !1;
	if (Cn) try {
		var Tn = {};
		Object.defineProperty(Tn, "passive", { get: function() {
			wn = !0;
		} }), window.addEventListener("test", Tn, Tn), window.removeEventListener("test", Tn, Tn);
	} catch {
		wn = !1;
	}
	var En = null, Dn = null, On = null;
	function kn() {
		if (On) return On;
		var e, t = Dn, n = t.length, r, i = "value" in En ? En.value : En.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return On = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function An(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function jn() {
		return !0;
	}
	function Mn() {
		return !1;
	}
	function Nn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? jn : Mn, this.isPropagationStopped = Mn, this;
		}
		return T(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = jn);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = jn);
			},
			persist: function() {},
			isPersistent: jn
		}), t;
	}
	var Pn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, Fn = Nn(Pn), In = T({}, Pn, {
		view: 0,
		detail: 0
	}), Ln = Nn(In), Rn, zn, Bn, Vn = T({}, In, {
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
		getModifierState: Qn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== Bn && (Bn && e.type === "mousemove" ? (Rn = e.screenX - Bn.screenX, zn = e.screenY - Bn.screenY) : zn = Rn = 0, Bn = e), Rn);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : zn;
		}
	}), Hn = Nn(Vn), Un = Nn(T({}, Vn, { dataTransfer: 0 })), Wn = Nn(T({}, In, { relatedTarget: 0 })), Gn = Nn(T({}, Pn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Kn = Nn(T({}, Pn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), qn = Nn(T({}, Pn, { data: 0 })), Jn = {
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
	}, Yn = {
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
	}, Xn = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Zn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Xn[e]) ? !!t[e] : !1;
	}
	function Qn() {
		return Zn;
	}
	var $n = Nn(T({}, In, {
		key: function(e) {
			if (e.key) {
				var t = Jn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = An(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Yn[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: Qn,
		charCode: function(e) {
			return e.type === "keypress" ? An(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? An(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), er = Nn(T({}, Vn, {
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
	})), tr = Nn(T({}, Pn, { submitter: 0 })), nr = Nn(T({}, In, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: Qn
	})), rr = Nn(T({}, Pn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), ir = Nn(T({}, Vn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), ar = Nn(T({}, Pn, {
		newState: 0,
		oldState: 0,
		source: 0
	})), or = [
		9,
		13,
		27,
		32
	], sr = Cn && "CompositionEvent" in window, cr = null;
	Cn && "documentMode" in document && (cr = document.documentMode);
	var lr = Cn && "TextEvent" in window && !cr, ur = Cn && (!sr || cr && 8 < cr && 11 >= cr), dr = " ", fr = !1;
	function pr(e, t) {
		switch (e) {
			case "keyup": return or.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function mr(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var hr = !1;
	function gr(e, t) {
		switch (e) {
			case "compositionend": return mr(t);
			case "keypress": return t.which === 32 ? (fr = !0, dr) : null;
			case "textInput": return e = t.data, e === dr && fr ? null : e;
			default: return null;
		}
	}
	function _r(e, t) {
		if (hr) return e === "compositionend" || !sr && pr(e, t) ? (e = kn(), On = Dn = En = null, hr = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return ur && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var H = {
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
	function vr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!H[e.type] : t === "textarea";
	}
	function yr(e, t, n, r) {
		_n ? vn ? vn.push(r) : vn = [r] : _n = r, t = qf(t, "onChange"), 0 < t.length && (n = new Fn("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var br = null, xr = null;
	function Sr(e) {
		Bf(e, 0);
	}
	function Cr(e) {
		if (Xt(Nt(e))) return e;
	}
	function wr(e, t) {
		if (e === "change") return t;
	}
	var Tr = !1;
	if (Cn) {
		var Er;
		if (Cn) {
			var Dr = "oninput" in document;
			if (!Dr) {
				var Or = document.createElement("div");
				Or.setAttribute("oninput", "return;"), Dr = typeof Or.oninput == "function";
			}
			Er = Dr;
		} else Er = !1;
		Tr = Er && (!document.documentMode || 9 < document.documentMode);
	}
	function kr() {
		br && (br.detachEvent("onpropertychange", Ar), xr = br = null);
	}
	function Ar(e) {
		if (e.propertyName === "value" && Cr(xr)) {
			var t = [];
			yr(t, xr, e, gn(e)), xn(Sr, t);
		}
	}
	function jr(e, t, n) {
		e === "focusin" ? (kr(), br = t, xr = n, br.attachEvent("onpropertychange", Ar)) : e === "focusout" && kr();
	}
	function Mr(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return Cr(xr);
	}
	function Nr(e, t) {
		if (e === "click") return Cr(t);
	}
	function Pr(e, t) {
		if (e === "input" || e === "change") return Cr(t);
	}
	function Fr(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var Ir = typeof Object.is == "function" ? Object.is : Fr;
	function Lr(e, t) {
		if (Ir(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!Fe.call(t, i) || !Ir(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Rr(e) {
		if (e ||= typeof document < "u" ? document : void 0, e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch {
			return e.body;
		}
	}
	function zr(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function Br(e, t) {
		var n = zr(e);
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
			n = zr(n);
		}
	}
	function Vr(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Vr(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function Hr(e) {
		e = e != null && e.ownerDocument != null && e.ownerDocument.defaultView != null ? e.ownerDocument.defaultView : window;
		for (var t = Rr(e.document); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = Rr(e.document);
		}
		return t;
	}
	function Wr(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	var Gr = Cn && "documentMode" in document && 11 >= document.documentMode, Kr = null, qr = null, Jr = null, Yr = !1;
	function Xr(e, t, n) {
		var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
		Yr || Kr == null || Kr !== Rr(r) || (r = Kr, "selectionStart" in r && Wr(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Jr && Lr(Jr, r) || (Jr = r, r = qf(qr, "onSelect"), 0 < r.length && (t = new Fn("onSelect", "select", null, t, n), e.push({
			event: t,
			listeners: r
		}), t.target = Kr)));
	}
	function Zr(e, t) {
		var n = {};
		return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
	}
	var Qr = {
		animationend: Zr("Animation", "AnimationEnd"),
		animationiteration: Zr("Animation", "AnimationIteration"),
		animationstart: Zr("Animation", "AnimationStart"),
		transitionrun: Zr("Transition", "TransitionRun"),
		transitionstart: Zr("Transition", "TransitionStart"),
		transitioncancel: Zr("Transition", "TransitionCancel"),
		transitionend: Zr("Transition", "TransitionEnd")
	}, $r = {}, ei = {};
	Cn && (ei = document.createElement("div").style, "AnimationEvent" in window || (delete Qr.animationend.animation, delete Qr.animationiteration.animation, delete Qr.animationstart.animation), "TransitionEvent" in window || delete Qr.transitionend.transition);
	function ti(e) {
		if ($r[e]) return $r[e];
		if (!Qr[e]) return e;
		var t = Qr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in ei) return $r[e] = t[n];
		return e;
	}
	var ni = ti("animationend"), ri = ti("animationiteration"), ii = ti("animationstart"), ai = ti("transitionrun"), oi = ti("transitionstart"), si = ti("transitioncancel"), ci = ti("transitionend"), li = /* @__PURE__ */ new Map(), ui = "abort auxClick beforeToggle cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error fullscreenChange fullscreenError gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	ui.push("scrollEnd");
	function di(e, t) {
		li.set(e, t), Lt(t, [e]);
	}
	var fi = 0;
	function pi(e, t) {
		if (e.name != null && e.name !== "auto") return e.name;
		if (t.autoName !== null) return t.autoName;
		e = xd.identifierPrefix;
		var n = fi++;
		return e = "_" + e + "t_" + n.toString(32) + "_", t.autoName = e;
	}
	function mi(e) {
		if (e == null || typeof e == "string") return e;
		var t = null, n = Od;
		if (n !== null) for (var r = 0; r < n.length; r++) {
			var i = e[n[r]];
			if (i != null) {
				if (i === "none") return "none";
				t = t == null ? i : t + (" " + i);
			}
		}
		return t ?? e.default;
	}
	function hi(e, t) {
		return e = mi(e), t = mi(t), t == null ? e === "auto" ? null : e : t === "auto" ? null : t;
	}
	var gi = typeof reportError == "function" ? reportError : function(e) {
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
	}, _i = [], vi = 0, yi = 0;
	function bi() {
		for (var e = vi, t = yi = vi = 0; t < e;) {
			var n = _i[t];
			_i[t++] = null;
			var r = _i[t];
			_i[t++] = null;
			var i = _i[t];
			_i[t++] = null;
			var a = _i[t];
			if (_i[t++] = null, r !== null && i !== null) {
				var o = r.pending;
				o === null ? i.next = i : (i.next = o.next, o.next = i), r.pending = i;
			}
			a !== 0 && wi(n, i, a);
		}
	}
	function xi(e, t, n, r) {
		_i[vi++] = e, _i[vi++] = t, _i[vi++] = n, _i[vi++] = r, yi |= r, e.lanes |= r, e = e.alternate, e !== null && (e.lanes |= r);
	}
	function Si(e, t, n, r) {
		return xi(e, t, n, r), Ti(e);
	}
	function Ci(e, t) {
		return xi(e, null, null, t), Ti(e);
	}
	function wi(e, t, n) {
		e.lanes |= n;
		var r = e.alternate;
		r !== null && (r.lanes |= n);
		for (var i = !1, a = e.return; a !== null;) a.childLanes |= n, r = a.alternate, r !== null && (r.childLanes |= n), a.tag === 22 && (e = a.stateNode, e === null || e._visibility & 1 || (i = !0)), e = a, a = a.return;
		return e.tag === 3 ? (a = e.stateNode, i && t !== null && (i = 31 - Qe(n), e = a.hiddenUpdates, r = e[i], r === null ? e[i] = [t] : r.push(t), t.lane = n | 536870912), a) : null;
	}
	function Ti(e) {
		if (50 < kd) throw kd = 0, Ad = null, Error(i(185));
		for (var t = e.return; t !== null;) e = t, t = e.return;
		return e.tag === 3 ? e.stateNode : null;
	}
	var Ei = {};
	function Di(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.refCleanup = this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function Oi(e, t, n, r) {
		return new Di(e, t, n, r);
	}
	function ki(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function Ai(e, t) {
		var n = e.alternate;
		return n === null ? (n = Oi(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 1206910976, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n.refCleanup = e.refCleanup, n;
	}
	function ji(e, t) {
		e.flags &= 1206910978;
		var n = e.alternate;
		return n === null ? (e.childLanes = 0, e.lanes = t, e.child = null, e.subtreeFlags = 0, e.memoizedProps = null, e.memoizedState = null, e.updateQueue = null, e.dependencies = null, e.stateNode = null) : (e.childLanes = n.childLanes, e.lanes = n.lanes, e.child = n.child, e.subtreeFlags = 0, e.deletions = null, e.memoizedProps = n.memoizedProps, e.memoizedState = n.memoizedState, e.updateQueue = n.updateQueue, e.type = n.type, t = n.dependencies, e.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}), e;
	}
	function Mi(e, t, n, r, a, o) {
		var s = 0;
		if (r = e, typeof r == "function") ki(r) && (s = 1);
		else if (typeof r == "string") s = qm(e, n, be.current) ? 26 : e === "html" || e === "head" || e === "body" ? 27 : 5;
		else a: switch (r) {
			case ie: return e = Oi(31, n, t, a), e.elementType = ie, e.lanes = o, e;
			case k: return Ni(n.children, a, o, t);
			case A:
				s = 8, a |= 24;
				break;
			case ee: return e = Oi(12, n, t, a | 2), e.elementType = ee, e.lanes = o, e;
			case ne: return e = Oi(13, n, t, a), e.elementType = ne, e.lanes = o, e;
			case N: return e = Oi(19, n, t, a), e.elementType = N, e.lanes = o, e;
			case ae:
			case se: return e = a | 32, e = Oi(30, n, t, e), e.elementType = se, e.lanes = o, e.stateNode = {
				autoName: null,
				paired: null,
				clones: null,
				ref: null
			}, e;
			default:
				if (typeof r == "object" && r) switch (r.$$typeof) {
					case te:
						s = 10;
						break a;
					case j:
						s = 9;
						break a;
					case M:
						s = 11;
						break a;
					case re:
						s = 14;
						break a;
					case P:
						s = 16, r = null;
						break a;
				}
				s = 29, n = Error(i(130, e === null ? "null" : typeof e, "")), r = null;
		}
		return t = Oi(s, n, t, a), t.elementType = e, t.type = r, t.lanes = o, t;
	}
	function Ni(e, t, n, r) {
		return e = Oi(7, e, r, t), e.lanes = n, e;
	}
	function Pi(e, t, n) {
		return e = Oi(6, e, null, t), e.lanes = n, e;
	}
	function Fi(e) {
		var t = Oi(18, null, null, 0);
		return t.stateNode = e, t;
	}
	function Ii(e, t, n) {
		return t = Oi(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	var Li = /* @__PURE__ */ new WeakMap();
	function Ri(e, t) {
		if (typeof e == "object" && e) {
			var n = Li.get(e);
			return n === void 0 ? (t = {
				value: e,
				source: t,
				stack: Pe(t)
			}, Li.set(e, t), t) : n;
		}
		return {
			value: e,
			source: t,
			stack: Pe(t)
		};
	}
	var zi = [], Bi = 0, Vi = null, Hi = 0, Ui = [], Wi = 0, Gi = null, Ki = 1, qi = "";
	function Ji(e, t) {
		zi[Bi++] = Hi, zi[Bi++] = Vi, Vi = e, Hi = t;
	}
	function Yi(e, t, n) {
		Ui[Wi++] = Ki, Ui[Wi++] = qi, Ui[Wi++] = Gi, Gi = e;
		var r = Ki;
		e = qi;
		var i = 32 - Qe(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - Qe(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, Ki = 1 << 32 - Qe(t) + i | n << i | r, qi = a + e;
		} else Ki = 1 << a | n << i | r, qi = e;
	}
	function Xi(e) {
		e.return !== null && (Ji(e, 1), Yi(e, 1, 0));
	}
	function Zi(e) {
		for (; e === Vi;) Vi = zi[--Bi], zi[Bi] = null, Hi = zi[--Bi], zi[Bi] = null;
		for (; e === Gi;) Gi = Ui[--Wi], Ui[Wi] = null, qi = Ui[--Wi], Ui[Wi] = null, Ki = Ui[--Wi], Ui[Wi] = null;
	}
	function Qi(e, t) {
		Ui[Wi++] = Ki, Ui[Wi++] = qi, Ui[Wi++] = Gi, Ki = t.id, qi = t.overflow, Gi = e;
	}
	var U = null, $i = null, W = !1, ea = null, ta = !1, na = Error(i(519));
	function ra(e) {
		throw la(Ri(Error(i(418, 1 < arguments.length && arguments[1] !== void 0 && arguments[1] ? "text" : "HTML", "")), e)), na;
	}
	function ia(e) {
		var t = e.stateNode, n = e.type, r = e.memoizedProps;
		switch (t[St] = e, t[Ct] = r, n) {
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
				$("invalid", t), en(t, r.value, r.defaultValue, r.checked, r.defaultChecked, r.type, r.name, !0);
				break;
			case "select":
				$("invalid", t);
				break;
			case "textarea": $("invalid", t), an(t, r.value, r.defaultValue, r.children);
		}
		n = r.children, typeof n != "string" && typeof n != "number" && typeof n != "bigint" || t.textContent === "" + n || !0 === r.suppressHydrationWarning || $f(t.textContent, n) ? (r.popover != null && ($("beforetoggle", t), $("toggle", t)), r.onScroll != null && $("scroll", t), r.onScrollEnd != null && $("scrollend", t), r.onClick != null && (t.onclick = mn), t = !0) : t = !1, t || ra(e, !0);
	}
	function aa(e) {
		for (U = e.return; U;) switch (U.tag) {
			case 5:
			case 31:
			case 13:
				ta = !1;
				return;
			case 27:
			case 3:
				ta = !0;
				return;
			default: U = U.return;
		}
	}
	function oa(e) {
		if (e !== U) return !1;
		if (!W) return aa(e), W = !0, !1;
		var t = e.tag, n;
		if ((n = t !== 3 && t !== 27) && ((n = t === 5) && (n = e.type, n = n === "form" || n === "button" || pp(e.type, e.memoizedProps)), n = !n), n && $i && ra(e), aa(e), t === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			$i = dm(e);
		} else if (t === 31) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(317));
			$i = dm(e);
		} else t === 27 ? (t = $i, Sp(e.type) ? (e = um, um = null, $i = e) : $i = t) : $i = U ? lm(e.stateNode.nextSibling) : null;
		return !0;
	}
	function sa() {
		$i = U = null, W = !1;
	}
	function ca() {
		var e = ea;
		return e !== null && (md === null ? md = e : md.push.apply(md, e), ea = null), e;
	}
	function la(e) {
		ea === null ? ea = [e] : ea.push(e);
	}
	var ua = _e(null), da = null, fa = null;
	function pa(e, t, n) {
		ye(ua, t._currentValue), t._currentValue = n;
	}
	function ma(e) {
		e._currentValue = ua.current, ve(ua);
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
					Ir(a.pendingProps.value, s.value) || (e === null ? e = [c] : e.push(c));
				}
			} else if (a === Ce.current) {
				if (s = a.alternate, s === null) throw Error(i(387));
				s.memoizedState.memoizedState !== a.memoizedState.memoizedState && (e === null ? e = [sh] : e.push(sh));
			}
			a = a.return;
		}
		return e !== null && ga(t, e, n, r), t.flags |= 262144, e !== null;
	}
	function va(e) {
		for (e = e.firstContext; e !== null;) {
			if (!Ir(e.context._currentValue, e.memoizedValue)) return !0;
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
	}, wa = t.unstable_scheduleCallback, Ta = t.unstable_NormalPriority, G = {
		$$typeof: te,
		Consumer: null,
		Provider: null,
		_currentValue: null,
		_currentValue2: null,
		_threadCount: 0
	};
	function Ea() {
		return {
			controller: new Ca(),
			data: /* @__PURE__ */ new Map(),
			refCount: 0
		};
	}
	function Da(e) {
		e.refCount--, e.refCount === 0 && wa(Ta, function() {
			e.controller.abort();
		});
	}
	function Oa(e, t) {
		if (e.pendingLanes & 4194048) {
			var n = e.transitionTypes;
			for (n === null && (n = e.transitionTypes = []), e = 0; e < t.length; e++) {
				var r = t[e];
				n.indexOf(r) === -1 && n.push(r);
			}
		}
	}
	var ka = null;
	function Aa(e) {
		var t = e.transitionTypes;
		return e.transitionTypes = null, t;
	}
	var ja = null, Ma = 0, Na = 0, Pa = null;
	function Fa(e, t) {
		if (ja === null) {
			var n = ja = [];
			Ma = 0, Na = Nf(), Pa = {
				status: "pending",
				value: void 0,
				then: function(e) {
					n.push(e);
				}
			};
		}
		return Ma++, t.then(Ia, Ia), t;
	}
	function Ia() {
		if (--Ma === 0 && (ka = null, ja !== null)) {
			Pa !== null && (Pa.status = "fulfilled");
			var e = ja;
			ja = null, Na = 0, Pa = null;
			for (var t = 0; t < e.length; t++) (0, e[t])();
		}
	}
	function La(e, t) {
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
	var Ra = F.S;
	F.S = function(e, t) {
		if (gd = Be(), typeof t == "object" && t && typeof t.then == "function" && Fa(e, t), ka !== null) for (var n = yf; n !== null;) Oa(n, ka), n = n.next;
		if (n = e.types, n !== null) {
			for (var r = yf; r !== null;) Oa(r, n), r = r.next;
			if (Na !== 0) {
				r = ka, r === null && (r = ka = []);
				for (var i = 0; i < n.length; i++) {
					var a = n[i];
					r.indexOf(a) === -1 && r.push(a);
				}
			}
		}
		Ra !== null && Ra(e, t);
	};
	var za = _e(null);
	function Ba() {
		var e = za.current;
		return e === null ? ed.pooledCache : e;
	}
	function Va(e, t) {
		t === null ? ye(za, za.current) : ye(za, t.pool);
	}
	function Ha() {
		var e = Ba();
		return e === null ? null : {
			parent: G._currentValue,
			pool: e
		};
	}
	var Ua = Error(i(460)), Wa = Error(i(474)), Ga = Error(i(542)), Ka = { then: function() {} };
	function qa(e) {
		return e = e.status, e === "fulfilled" || e === "rejected";
	}
	function Ja(e, t, n) {
		switch (n = e[n], n === void 0 ? e.push(t) : n !== t && (t.then(mn, mn), t = n), t.status) {
			case "fulfilled": return t.value;
			case "rejected": throw e = t.reason, Qa(e), e === void 0 && !("reason" in t) ? Error(i(600)) : e;
			default:
				if (typeof t.status == "string") t.then(mn, mn);
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
					case "rejected": throw e = t.reason, Qa(e), e;
				}
				throw Xa = t, Ua;
		}
	}
	function Ya(e) {
		try {
			var t = e._init;
			return t(e._payload);
		} catch (e) {
			throw typeof e == "object" && e && typeof e.then == "function" ? (Xa = e, Ua) : e;
		}
	}
	var Xa = null;
	function Za() {
		if (Xa === null) throw Error(i(459));
		var e = Xa;
		return Xa = null, e;
	}
	function Qa(e) {
		if (e === Ua || e === Ga) throw Error(i(483));
	}
	var $a = null, eo = 0;
	function to(e) {
		var t = eo;
		return eo += 1, $a === null && ($a = []), Ja($a, e, t);
	}
	function no(e, t) {
		t = t.props.ref, e.ref = t === void 0 ? null : t;
	}
	function ro(e, t) {
		throw t.$$typeof === E ? Error(i(525)) : (e = Object.prototype.toString.call(t), Error(i(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e)));
	}
	function io(e) {
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
			return e = Ai(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 134217730, n) : (r = r.index, r < n ? (t.flags |= 2, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 134217730), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = Pi(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === k ? (e = d(e, t, n.props.children, r, n.key), no(e, n), e) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === P && Ya(i) === t.type) ? (t = a(t, n.props), no(t, n), t.return = e, t) : (t = Mi(n.type, n.key, n.props, null, e.mode, r), no(t, n), t.return = e, t);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = Ii(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = Ni(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number" || typeof t == "bigint") return t = Pi("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case D: return n = Mi(t.type, t.key, t.props, null, e.mode, n), no(n, t), n.return = e, n;
					case O: return t = Ii(t, e.mode, n), t.return = e, t;
					case P: return t = Ya(t), f(e, t, n);
				}
				if (pe(t) || ue(t)) return t = Ni(t, e.mode, n, null), t.return = e, t;
				if (typeof t.then == "function") return f(e, to(t), n);
				if (t.$$typeof === te) return f(e, xa(e, t), n);
				ro(e, t);
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
					case P: return n = Ya(n), p(e, t, n, r);
				}
				if (pe(n) || ue(n)) return i === null ? d(e, t, n, r, null) : null;
				if (typeof n.then == "function") return p(e, t, to(n), r);
				if (n.$$typeof === te) return p(e, t, xa(e, n), r);
				ro(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number" || typeof r == "bigint") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case D: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case O: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case P: return r = Ya(r), m(e, t, n, r, i);
				}
				if (pe(r) || ue(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				if (typeof r.then == "function") return m(e, t, n, to(r), i);
				if (r.$$typeof === te) return m(e, t, n, xa(t, r), i);
				ro(t, r);
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
			if (h === s.length) return n(i, d), W && Ji(i, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(i, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return W && Ji(i, h), l;
			}
			for (d = r(d); h < s.length; h++) g = m(d, i, h, s[h], c), g !== null && (e && (_ = g.alternate, _ !== null && d.delete(_.key === null ? h : _.key)), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(i, e);
			}), W && Ji(i, h), l;
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
			if (v.done) return n(a, h), W && Ji(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return W && Ji(a, g), u;
			}
			for (h = r(h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && (_ = v.alternate, _ !== null && h.delete(_.key === null ? g : _.key)), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), W && Ji(a, g), u;
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
											n(e, r.sibling), c = a(r, o.props.children), no(c, o), c.return = e, e = c;
											break a;
										}
									} else if (r.elementType === l || typeof l == "object" && l && l.$$typeof === P && Ya(l) === r.type) {
										n(e, r.sibling), c = a(r, o.props), no(c, o), c.return = e, e = c;
										break a;
									}
									n(e, r);
									break;
								}
								t(e, r), r = r.sibling;
							}
							o.type === k ? (c = Ni(o.props.children, e.mode, c, o.key), no(c, o), c.return = e, e = c) : (c = Mi(o.type, o.key, o.props, null, e.mode, c), no(c, o), c.return = e, e = c);
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
							c = Ii(o, e.mode, c), c.return = e, e = c;
						}
						return s(e);
					case P: return o = Ya(o), _(e, r, o, c);
				}
				if (pe(o)) return h(e, r, o, c);
				if (ue(o)) {
					if (l = ue(o), typeof l != "function") throw Error(i(150));
					return o = l.call(o), g(e, r, o, c);
				}
				if (typeof o.then == "function") return _(e, r, to(o), c);
				if (o.$$typeof === te) return _(e, r, xa(e, o), c);
				ro(e, o);
			}
			return typeof o == "string" && o !== "" || typeof o == "number" || typeof o == "bigint" ? (o = "" + o, r !== null && r.tag === 6 ? (n(e, r.sibling), c = a(r, o), c.return = e, e = c) : (n(e, r), c = Pi(o, e.mode, c), c.return = e, e = c), s(e)) : n(e, r);
		}
		return function(e, t, n, r) {
			try {
				eo = 0;
				var i = _(e, t, n, r);
				return $a = null, i;
			} catch (t) {
				if (t === Ua || t === Ga) throw t;
				var a = Oi(29, t, null, e.mode);
				return a.lanes = r, a.return = e, a;
			}
		};
	}
	var ao = io(!0), oo = io(!1), so = !1;
	function co(e) {
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
	function lo(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			callbacks: null
		});
	}
	function uo(e) {
		return {
			lane: e,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function fo(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, $u & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, t = Ti(e), wi(e, null, n), t;
		}
		return xi(e, r, t, n), Ti(e);
	}
	function po(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194048)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, ht(e, n);
		}
	}
	function mo(e, t) {
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
	var ho = !1;
	function go() {
		if (ho) {
			var e = Pa;
			if (e !== null) throw e;
		}
	}
	function _o(e, t, n, r) {
		ho = !1;
		var i = e.updateQueue;
		so = !1;
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
					f !== 0 && f === Na && (ho = !0), u !== null && (u = u.next = {
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
							case 2: so = !0;
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
			u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, a === null && (i.shared.lanes = 0), cd |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function vo(e, t) {
		if (typeof e != "function") throw Error(i(191, e));
		e.call(t);
	}
	function yo(e, t) {
		var n = e.callbacks;
		if (n !== null) for (e.callbacks = null, e = 0; e < n.length; e++) vo(n[e], t);
	}
	var bo = _e(null), xo = _e(0);
	function So(e, t) {
		e = od, ye(xo, e), ye(bo, t), od = e | t.baseLanes;
	}
	function Co() {
		ye(xo, od), ye(bo, bo.current);
	}
	function wo() {
		od = xo.current, ve(bo), ve(xo);
	}
	var To = _e(null), Eo = null;
	function Do(e) {
		var t = e.alternate;
		ye(Mo, Mo.current & 1), ye(To, e), Eo === null && (t === null || bo.current !== null || t.memoizedState !== null) && (Eo = e);
	}
	function Oo(e) {
		ye(Mo, Mo.current), ye(To, e), Eo === null && (Eo = e);
	}
	function ko(e) {
		e.tag === 22 ? (ye(Mo, Mo.current), ye(To, e), Eo === null && (Eo = e)) : Ao();
	}
	function Ao() {
		ye(Mo, Mo.current), ye(To, To.current);
	}
	function jo(e) {
		ve(To), Eo === e && (Eo = null), ve(Mo);
	}
	var Mo = _e(0);
	function No(e, t) {
		ye(To, To.current), ye(Mo, t);
	}
	function Po(e) {
		ve(Mo), ve(To), Eo === e && (Eo = null);
	}
	function Fo(e) {
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
	var Io = 0, K = null, Lo = null, Ro = null, zo = !1, Bo = !1, Vo = !1, Ho = 0, Uo = 0, Wo = null, Go = 0;
	function Ko() {
		throw Error(i(321));
	}
	function qo(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!Ir(e[n], t[n])) return !1;
		return !0;
	}
	function Jo(e, t, n, r, i, a) {
		return Io = a, K = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, F.H = e === null || e.memoizedState === null ? dc : fc, Vo = !1, a = n(r, i), Vo = !1, Bo && (a = Xo(t, n, r, i)), Yo(e), a;
	}
	function Yo(e) {
		F.H = uc;
		var t = Lo !== null && Lo.next !== null;
		if (Io = 0, Ro = Lo = K = null, zo = !1, Uo = 0, Wo = null, t) throw Error(i(300));
		e === null || kc || (e = e.dependencies, e !== null && va(e) && (kc = !0));
	}
	function Xo(e, t, n, r) {
		K = e;
		var a = 0;
		do {
			if (Bo && (Wo = null), Uo = 0, Bo = !1, 25 <= a) throw Error(i(301));
			if (a += 1, Ro = Lo = null, e.updateQueue != null) {
				var o = e.updateQueue;
				o.lastEffect = null, o.events = null, o.stores = null, o.memoCache != null && (o.memoCache.index = 0);
			}
			F.H = pc, o = t(n, r);
		} while (Bo);
		return o;
	}
	function Zo() {
		var e = F.H, t = e.useState()[0];
		return t = typeof t.then == "function" ? is(t) : t, e = e.useState()[0], (Lo === null ? null : Lo.memoizedState) !== e && (K.flags |= 1024), t;
	}
	function Qo() {
		var e = Ho !== 0;
		return Ho = 0, e;
	}
	function $o(e, t, n) {
		t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~n;
	}
	function es(e) {
		if (zo) {
			for (e = e.memoizedState; e !== null;) {
				var t = e.queue;
				t !== null && (t.pending = null), e = e.next;
			}
			zo = !1;
		}
		Io = 0, Ro = Lo = K = null, Bo = !1, Uo = Ho = 0, Wo = null;
	}
	function ts() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return Ro === null ? K.memoizedState = Ro = e : Ro = Ro.next = e, Ro;
	}
	function ns() {
		if (Lo === null) {
			var e = K.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = Lo.next;
		var t = Ro === null ? K.memoizedState : Ro.next;
		if (t !== null) Ro = t, Lo = e;
		else {
			if (e === null) throw K.alternate === null ? Error(i(467)) : Error(i(310));
			Lo = e, e = {
				memoizedState: Lo.memoizedState,
				baseState: Lo.baseState,
				baseQueue: Lo.baseQueue,
				queue: Lo.queue,
				next: null
			}, Ro === null ? K.memoizedState = Ro = e : Ro = Ro.next = e;
		}
		return Ro;
	}
	function rs() {
		return {
			lastEffect: null,
			events: null,
			stores: null,
			memoCache: null
		};
	}
	function is(e) {
		var t = Uo;
		return Uo += 1, Wo === null && (Wo = []), e = Ja(Wo, e, t), t = K, (Ro === null ? t.memoizedState : Ro.next) === null && (t = t.alternate, F.H = t === null || t.memoizedState === null ? dc : fc), e;
	}
	function as(e) {
		if (typeof e == "object" && e) {
			if (typeof e.then == "function") return is(e);
			if (e.$$typeof === ce) return;
			if (e.$$typeof === te) return ba(e);
		}
		throw Error(i(438, String(e)));
	}
	function os(e) {
		var t = null, n = K.updateQueue;
		if (n !== null && (t = n.memoCache), t == null) {
			var r = K.alternate;
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
		}, n === null && (n = rs(), K.updateQueue = n), n.memoCache = t, n = t.data[t.index], n === void 0) for (n = t.data[t.index] = Array(e), r = 0; r < e; r++) n[r] = oe;
		return t.index++, n;
	}
	function ss(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function cs(e) {
		return ls(ns(), Lo, e);
	}
	function ls(e, t, n) {
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
				if (f === u.lane ? (Io & f) === f : (J & f) === f) {
					var p = u.revertLane;
					if (p === 0) l !== null && (l = l.next = {
						lane: 0,
						revertLane: 0,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}), f === Na && (d = !0);
					else if ((Io & p) === p) {
						u = u.next, p === Na && (d = !0);
						continue;
					} else f = {
						lane: 0,
						revertLane: u.revertLane,
						gesture: null,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					}, l === null ? (c = l = f, s = o) : l = l.next = f, K.lanes |= p, cd |= p;
					f = u.action, Vo && n(o, f), o = u.hasEagerState ? u.eagerState : n(o, f);
				} else p = {
					lane: f,
					revertLane: u.revertLane,
					gesture: u.gesture,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}, l === null ? (c = l = p, s = o) : l = l.next = p, K.lanes |= f, cd |= f;
				u = u.next;
			} while (u !== null && u !== t);
			if (l === null ? s = o : l.next = c, !Ir(o, e.memoizedState) && (kc = !0, d && (n = Pa, n !== null))) throw n;
			e.memoizedState = o, e.baseState = s, e.baseQueue = l, r.lastRenderedState = o;
		}
		return a === null && (r.lanes = 0), [e.memoizedState, r.dispatch];
	}
	function us(e) {
		var t = ns(), n = t.queue;
		if (n === null) throw Error(i(311));
		n.lastRenderedReducer = e;
		var r = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			Ir(o, t.memoizedState) || (kc = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, r];
	}
	function ds(e, t, n) {
		var r = K, a = ns(), o = W;
		if (o) {
			if (n === void 0) throw Error(i(407));
			n = n();
		} else n = t();
		var s = !Ir((Lo || a).memoizedState, n);
		if (s && (a.memoizedState = n, kc = !0), a = a.queue, Is(ms.bind(null, r, a, e), [e]), e = a.getSnapshot !== t || s || Ro !== null && !!(Ro.memoizedState.tag & 1), js(e ? 9 : 8, { destroy: void 0 }, ps.bind(null, r, a, n, t), null), e) {
			if (r.flags |= 2048, ed === null) throw Error(i(349));
			o || Io & 127 || fs(r, t, n);
		}
		return n;
	}
	function fs(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = K.updateQueue, t === null ? (t = rs(), K.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function ps(e, t, n, r) {
		t.value = n, t.getSnapshot = r, hs(t) && gs(e);
	}
	function ms(e, t, n) {
		return n(function() {
			hs(t) && gs(e);
		});
	}
	function hs(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !Ir(e, n);
		} catch {
			return !0;
		}
	}
	function gs(e) {
		var t = Ci(e, 2);
		t !== null && Nd(t, e, 2);
	}
	function _s(e) {
		var t = ts();
		if (typeof e == "function") {
			var n = e;
			if (e = n(), Vo) {
				Ze(!0);
				try {
					n();
				} finally {
					Ze(!1);
				}
			}
		}
		return t.memoizedState = t.baseState = e, t.queue = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: ss,
			lastRenderedState: e
		}, t;
	}
	function vs(e, t, n, r) {
		return e.baseState = n, ls(e, Lo, typeof r == "function" ? r : ss);
	}
	function ys(e, t, n, r, a) {
		if (sc(e)) throw Error(i(485));
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
			F.T === null ? o.isTransition = !1 : n(!0), r(o), n = t.pending, n === null ? (o.next = t.pending = o, bs(t, o)) : (o.next = n.next, t.pending = n.next = o);
		}
	}
	function bs(e, t) {
		var n = t.action, r = t.payload, i = e.state;
		if (t.isTransition) {
			var a = F.T, o = {};
			o.types = a === null ? null : a.types, F.T = o;
			try {
				var s = n(i, r), c = F.S;
				c !== null && c(o, s), xs(e, t, s);
			} catch (n) {
				Cs(e, t, n);
			} finally {
				a !== null && o.types !== null && (a.types = o.types), F.T = a;
			}
		} else try {
			a = n(i, r), xs(e, t, a);
		} catch (n) {
			Cs(e, t, n);
		}
	}
	function xs(e, t, n) {
		typeof n == "object" && n && typeof n.then == "function" ? n.then(function(n) {
			Ss(e, t, n);
		}, function(n) {
			return Cs(e, t, n);
		}) : Ss(e, t, n);
	}
	function Ss(e, t, n) {
		t.status = "fulfilled", t.value = n, ws(t), e.state = n, t = e.pending, t !== null && (n = t.next, n === t ? e.pending = null : (n = n.next, t.next = n, bs(e, n)));
	}
	function Cs(e, t, n) {
		var r = e.pending;
		if (e.pending = null, r !== null) {
			r = r.next;
			do
				t.status = "rejected", t.reason = n, ws(t), t = t.next;
			while (t !== r);
		}
		e.action = null;
	}
	function ws(e) {
		e = e.listeners;
		for (var t = 0; t < e.length; t++) (0, e[t])();
	}
	function Ts(e, t) {
		return t;
	}
	function Es(e, t) {
		if (W) {
			var n = ed.formState;
			if (n !== null) {
				a: {
					var r = K;
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
		return n = ts(), n.memoizedState = n.baseState = t, r = {
			pending: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Ts,
			lastRenderedState: t
		}, n.queue = r, n = ic.bind(null, K, r), r.dispatch = n, r = _s(!1), a = oc.bind(null, K, !1, r.queue), r = ts(), i = {
			state: t,
			dispatch: null,
			action: e,
			pending: null
		}, r.queue = i, n = ys.bind(null, K, i, a, n), i.dispatch = n, r.memoizedState = e, [
			t,
			n,
			!1
		];
	}
	function Ds(e) {
		return Os(ns(), Lo, e);
	}
	function Os(e, t, n) {
		if (t = ls(e, t, Ts)[0], e = cs(ss)[0], typeof t == "object" && t && typeof t.then == "function") try {
			var r = is(t);
		} catch (e) {
			throw e === Ua ? Ga : e;
		}
		else r = t;
		t = ns();
		var i = t.queue, a = i.dispatch;
		return n !== t.memoizedState && (K.flags |= 2048, js(9, { destroy: void 0 }, ks.bind(null, i, n), null)), [
			r,
			a,
			e
		];
	}
	function ks(e, t) {
		e.action = t;
	}
	function As(e) {
		var t = ns(), n = Lo;
		if (n !== null) return Os(t, n, e);
		ns(), t = t.memoizedState, n = ns();
		var r = n.queue.dispatch;
		return n.memoizedState = e, [
			t,
			r,
			!1
		];
	}
	function js(e, t, n, r) {
		return e = {
			tag: e,
			create: n,
			deps: r,
			inst: t,
			next: null
		}, t = K.updateQueue, t === null && (t = rs(), K.updateQueue = t), n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e), e;
	}
	function Ms() {
		return ns().memoizedState;
	}
	function Ns(e, t, n, r) {
		var i = ts();
		K.flags |= e, i.memoizedState = js(1 | t, { destroy: void 0 }, n, r === void 0 ? null : r);
	}
	function Ps(e, t, n, r) {
		var i = ns();
		r = r === void 0 ? null : r;
		var a = i.memoizedState.inst;
		Lo !== null && r !== null && qo(r, Lo.memoizedState.deps) ? i.memoizedState = js(t, a, n, r) : (K.flags |= e, i.memoizedState = js(1 | t, a, n, r));
	}
	function Fs(e, t) {
		Ns(8390656, 8, e, t);
	}
	function Is(e, t) {
		Ps(2048, 8, e, t);
	}
	function Ls(e) {
		K.flags |= 4;
		var t = K.updateQueue;
		if (t === null) t = rs(), K.updateQueue = t, t.events = [e];
		else {
			var n = t.events;
			n === null ? t.events = [e] : n.push(e);
		}
	}
	function Rs(e) {
		var t = ns().memoizedState;
		return Ls({
			ref: t,
			nextImpl: e
		}), function() {
			if ($u & 2) throw Error(i(440));
			return t.impl.apply(void 0, arguments);
		};
	}
	function zs(e, t) {
		return Ps(4, 2, e, t);
	}
	function Bs(e, t) {
		return Ps(4, 4, e, t);
	}
	function Vs(e, t) {
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
	function Hs(e, t, n) {
		n = n == null ? null : n.concat([e]), Ps(4, 4, Vs.bind(null, t, e), n);
	}
	function Us() {}
	function Ws(e, t) {
		var n = ns();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return t !== null && qo(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function Gs(e, t) {
		var n = ns();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		if (t !== null && qo(t, r[1])) return r[0];
		if (r = e(), Vo) {
			Ze(!0);
			try {
				e();
			} finally {
				Ze(!1);
			}
		}
		return n.memoizedState = [r, t], r;
	}
	function Ks(e, t, n) {
		return n === void 0 || Io & 1073741824 && !(J & 261930) ? e.memoizedState = t : (e.memoizedState = n, e = Md(), K.lanes |= e, cd |= e, n);
	}
	function qs(e, t, n, r) {
		return Ir(n, t) ? n : bo.current === null ? !(Io & 106) || Io & 1073741824 && !(J & 261930) ? (kc = !0, e.memoizedState = n) : (e = Md(), K.lanes |= e, cd |= e, t) : (e = Ks(e, n, r), Ir(e, t) || (kc = !0), e);
	}
	function Js(e, t, n, r, i) {
		var a = I.p;
		I.p = a !== 0 && 8 > a ? a : 8;
		var o = F.T, s = {};
		s.types = o === null ? null : o.types, F.T = s, oc(e, !1, t, n);
		try {
			var c = i(), l = F.S;
			l !== null && l(s, c), typeof c == "object" && c && typeof c.then == "function" ? ac(e, t, La(c, r), jd(e)) : ac(e, t, r, jd(e));
		} catch (n) {
			ac(e, t, {
				then: function() {},
				status: "rejected",
				reason: n
			}, jd());
		} finally {
			I.p = a, o !== null && s.types !== null && (o.types = s.types), F.T = o;
		}
	}
	function Ys() {}
	function Xs(e, t, n, r) {
		if (e.tag !== 5) throw Error(i(476));
		var a = Zs(e).queue;
		Js(e, a, t, me, n === null ? Ys : function() {
			return Qs(e), n(r);
		});
	}
	function Zs(e) {
		var t = e.memoizedState;
		if (t !== null) return t;
		t = {
			memoizedState: me,
			baseState: me,
			baseQueue: null,
			queue: {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: ss,
				lastRenderedState: me
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
				lastRenderedReducer: ss,
				lastRenderedState: n
			},
			next: null
		}, e.memoizedState = t, e = e.alternate, e !== null && (e.memoizedState = t), t;
	}
	function Qs(e) {
		var t = Zs(e);
		t.next === null && (t = e.alternate.memoizedState), ac(e, t.next.queue, {}, jd());
	}
	function $s() {
		return ba(sh);
	}
	function ec() {
		return ns().memoizedState;
	}
	function tc() {
		return ns().memoizedState;
	}
	function nc(e) {
		for (var t = e.return; t !== null;) {
			switch (t.tag) {
				case 24:
				case 3:
					var n = jd();
					e = uo(n);
					var r = fo(t, e, n);
					r !== null && (Nd(r, t, n), po(r, t, n)), t = { cache: Ea() }, e.payload = t;
					return;
			}
			t = t.return;
		}
	}
	function rc(e, t, n) {
		var r = jd();
		n = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, sc(e) ? cc(t, n) : (n = Si(e, t, n, r), n !== null && (Nd(n, e, r), lc(n, t, r)));
	}
	function ic(e, t, n) {
		ac(e, t, n, jd());
	}
	function ac(e, t, n, r) {
		var i = {
			lane: r,
			revertLane: 0,
			gesture: null,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (sc(e)) cc(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, Ir(s, o)) return xi(e, t, i, 0), ed === null && bi(), !1;
			} catch {}
			if (n = Si(e, t, i, r), n !== null) return Nd(n, e, r), lc(n, t, r), !0;
		}
		return !1;
	}
	function oc(e, t, n, r) {
		if (r = {
			lane: 2,
			revertLane: Nf(),
			gesture: null,
			action: r,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, sc(e)) {
			if (t) throw Error(i(479));
		} else t = Si(e, n, r, 2), t !== null && Nd(t, e, 2);
	}
	function sc(e) {
		var t = e.alternate;
		return e === K || t !== null && t === K;
	}
	function cc(e, t) {
		Bo = zo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function lc(e, t, n) {
		if (n & 4194048) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, ht(e, n);
		}
	}
	var uc = {
		readContext: ba,
		use: as,
		useCallback: Ko,
		useContext: Ko,
		useEffect: Ko,
		useImperativeHandle: Ko,
		useLayoutEffect: Ko,
		useInsertionEffect: Ko,
		useMemo: Ko,
		useReducer: Ko,
		useRef: Ko,
		useState: Ko,
		useDebugValue: Ko,
		useDeferredValue: Ko,
		useTransition: Ko,
		useSyncExternalStore: Ko,
		useId: Ko,
		useHostTransitionStatus: Ko,
		useFormState: Ko,
		useActionState: Ko,
		useOptimistic: Ko,
		useMemoCache: Ko,
		useCacheRefresh: Ko,
		useEffectEvent: Ko
	}, dc = {
		readContext: ba,
		use: as,
		useCallback: function(e, t) {
			return ts().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: ba,
		useEffect: Fs,
		useImperativeHandle: function(e, t, n) {
			n = n == null ? null : n.concat([e]), Ns(4194308, 4, Vs.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return Ns(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			Ns(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = ts();
			t = t === void 0 ? null : t;
			var r = e();
			if (Vo) {
				Ze(!0);
				try {
					e();
				} finally {
					Ze(!1);
				}
			}
			return n.memoizedState = [r, t], r;
		},
		useReducer: function(e, t, n) {
			var r = ts();
			if (n !== void 0) {
				var i = n(t);
				if (Vo) {
					Ze(!0);
					try {
						n(t);
					} finally {
						Ze(!1);
					}
				}
			} else i = t;
			return r.memoizedState = r.baseState = i, e = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: i
			}, r.queue = e, e = e.dispatch = rc.bind(null, K, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = ts();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: function(e) {
			e = _s(e);
			var t = e.queue, n = ic.bind(null, K, t);
			return t.dispatch = n, [e.memoizedState, n];
		},
		useDebugValue: Us,
		useDeferredValue: function(e, t) {
			return Ks(ts(), e, t);
		},
		useTransition: function() {
			var e = _s(!1);
			return e = Js.bind(null, K, e.queue, !0, !1), ts().memoizedState = e, [!1, e];
		},
		useSyncExternalStore: function(e, t, n) {
			var r = K, a = ts();
			if (W) {
				if (n === void 0) throw Error(i(407));
				n = n();
			} else {
				if (n = t(), ed === null) throw Error(i(349));
				J & 127 || fs(r, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, Fs(ms.bind(null, r, o, e), [e]), r.flags |= 2048, js(9, { destroy: void 0 }, ps.bind(null, r, o, n, t), null), n;
		},
		useId: function() {
			var e = ts(), t = ed.identifierPrefix;
			if (W) {
				var n = qi, r = Ki;
				n = (r & ~(1 << 32 - Qe(r) - 1)).toString(32) + n, t = "_" + t + "R_" + n, n = Ho++, 0 < n && (t += "H" + n.toString(32)), t += "_";
			} else n = Go++, t = "_" + t + "r_" + n.toString(32) + "_";
			return e.memoizedState = t;
		},
		useHostTransitionStatus: $s,
		useFormState: Es,
		useActionState: Es,
		useOptimistic: function(e) {
			var t = ts();
			t.memoizedState = t.baseState = e;
			var n = {
				pending: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: null,
				lastRenderedState: null
			};
			return t.queue = n, t = oc.bind(null, K, !0, n), n.dispatch = t, [e, t];
		},
		useMemoCache: os,
		useCacheRefresh: function() {
			return ts().memoizedState = nc.bind(null, K);
		},
		useEffectEvent: function(e) {
			var t = ts(), n = { impl: e };
			return t.memoizedState = n, function() {
				if ($u & 2) throw Error(i(440));
				return n.impl.apply(void 0, arguments);
			};
		}
	}, fc = {
		readContext: ba,
		use: as,
		useCallback: Ws,
		useContext: ba,
		useEffect: Is,
		useImperativeHandle: Hs,
		useInsertionEffect: zs,
		useLayoutEffect: Bs,
		useMemo: Gs,
		useReducer: cs,
		useRef: Ms,
		useState: function() {
			return cs(ss);
		},
		useDebugValue: Us,
		useDeferredValue: function(e, t) {
			return qs(ns(), Lo.memoizedState, e, t);
		},
		useTransition: function() {
			var e = cs(ss)[0], t = ns().memoizedState;
			return [typeof e == "boolean" ? e : is(e), t];
		},
		useSyncExternalStore: ds,
		useId: ec,
		useHostTransitionStatus: $s,
		useFormState: Ds,
		useActionState: Ds,
		useOptimistic: function(e, t) {
			return vs(ns(), Lo, e, t);
		},
		useMemoCache: os,
		useCacheRefresh: tc,
		useEffectEvent: Rs
	}, pc = {
		readContext: ba,
		use: as,
		useCallback: Ws,
		useContext: ba,
		useEffect: Is,
		useImperativeHandle: Hs,
		useInsertionEffect: zs,
		useLayoutEffect: Bs,
		useMemo: Gs,
		useReducer: us,
		useRef: Ms,
		useState: function() {
			return us(ss);
		},
		useDebugValue: Us,
		useDeferredValue: function(e, t) {
			var n = ns();
			return Lo === null ? Ks(n, e, t) : qs(n, Lo.memoizedState, e, t);
		},
		useTransition: function() {
			var e = us(ss)[0], t = ns().memoizedState;
			return [typeof e == "boolean" ? e : is(e), t];
		},
		useSyncExternalStore: ds,
		useId: ec,
		useHostTransitionStatus: $s,
		useFormState: As,
		useActionState: As,
		useOptimistic: function(e, t) {
			var n = ns();
			return Lo === null ? (n.baseState = e, [e, n.queue.dispatch]) : vs(n, Lo, e, t);
		},
		useMemoCache: os,
		useCacheRefresh: tc,
		useEffectEvent: Rs
	};
	function mc(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : T({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var hc = {
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = jd(), i = uo(r);
			i.payload = t, n != null && (i.callback = n), t = fo(e, i, r), t !== null && (Nd(t, e, r), po(t, e, r));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = jd(), i = uo(r);
			i.tag = 1, i.payload = t, n != null && (i.callback = n), t = fo(e, i, r), t !== null && (Nd(t, e, r), po(t, e, r));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = jd(), r = uo(n);
			r.tag = 2, t != null && (r.callback = t), t = fo(e, r, n), t !== null && (Nd(t, e, n), po(t, e, n));
		}
	};
	function gc(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !Lr(n, r) || !Lr(i, a) : !0;
	}
	function _c(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && hc.enqueueReplaceState(t, t.state, null);
	}
	function vc(e, t) {
		var n = t;
		if ("ref" in t) for (var r in n = {}, t) r !== "ref" && (n[r] = t[r]);
		if (e = e.defaultProps) for (var i in n === t && (n = T({}, n)), e) n[i] === void 0 && (n[i] = e[i]);
		return n;
	}
	function yc(e) {
		gi(e);
	}
	function bc(e) {
		console.error(e);
	}
	function xc(e) {
		gi(e);
	}
	function Sc(e, t) {
		try {
			var n = e.onUncaughtError;
			n(t.value, { componentStack: t.stack });
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	function Cc(e, t, n) {
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
	function wc(e, t, n) {
		return n = uo(n), n.tag = 3, n.payload = { element: null }, n.callback = function() {
			Sc(e, t);
		}, n;
	}
	function Tc(e) {
		return e = uo(e), e.tag = 3, e;
	}
	function Ec(e, t, n, r) {
		var i = n.type.getDerivedStateFromError;
		if (typeof i == "function") {
			var a = r.value;
			e.payload = function() {
				return i(a);
			}, e.callback = function() {
				Cc(t, n, r);
			};
		}
		var o = n.stateNode;
		o !== null && typeof o.componentDidCatch == "function" && (e.callback = function() {
			Cc(t, n, r), typeof i != "function" && (yd === null ? yd = /* @__PURE__ */ new Set([this]) : yd.add(this));
			var e = r.stack;
			this.componentDidCatch(r.value, { componentStack: e === null ? "" : e });
		});
	}
	function Dc(e, t, n, r, a) {
		if (n.flags |= 32768, typeof r == "object" && r && typeof r.then == "function") {
			if (t = n.alternate, t !== null && _a(t, n, a, !0), n = To.current, n !== null) {
				switch (n.tag) {
					case 31:
					case 13:
					case 19: return Eo === null ? Gd() : n.alternate === null && sd === 0 && (sd = 3), n.flags &= -257, n.flags |= 65536, n.lanes = a, r === Ka ? n.flags |= 16384 : (t = n.updateQueue, t === null ? n.updateQueue = /* @__PURE__ */ new Set([r]) : t.add(r), pf(e, r, a)), !1;
					case 22: return n.flags |= 65536, r === Ka ? n.flags |= 16384 : (t = n.updateQueue, t === null ? (t = {
						transitions: null,
						markerInstances: null,
						retryQueue: /* @__PURE__ */ new Set([r])
					}, n.updateQueue = t) : (n = t.retryQueue, n === null ? t.retryQueue = /* @__PURE__ */ new Set([r]) : n.add(r)), pf(e, r, a)), !1;
				}
				throw Error(i(435, n.tag));
			}
			return pf(e, r, a), Gd(), !1;
		}
		if (W) return t = To.current, t === null ? (r !== na && (t = Error(i(423), { cause: r }), la(Ri(t, n))), e = e.current.alternate, e.flags |= 65536, a &= -a, e.lanes |= a, r = Ri(r, n), a = wc(e.stateNode, r, a), mo(e, a), sd !== 4 && (sd = 2)) : (!(t.flags & 65536) && (t.flags |= 256), t.flags |= 65536, t.lanes = a, r !== na && (e = Error(i(422), { cause: r }), la(Ri(e, n)))), !1;
		var o = Error(i(520), { cause: r });
		if (o = Ri(o, n), pd === null ? pd = [o] : pd.push(o), sd !== 4 && (sd = 2), t === null) return !0;
		r = Ri(r, n), n = t;
		do {
			switch (n.tag) {
				case 3: return n.flags |= 65536, e = a & -a, n.lanes |= e, e = wc(n.stateNode, r, e), mo(n, e), !1;
				case 1:
					if (t = n.type, o = n.stateNode, !(n.flags & 128) && (typeof t.getDerivedStateFromError == "function" || o !== null && typeof o.componentDidCatch == "function" && (yd === null || !yd.has(o)))) return n.flags |= 65536, a &= -a, n.lanes |= a, a = Tc(a), Ec(a, e, n, r), mo(n, a), !1;
					break;
				case 22: if (n.memoizedState !== null) return n.flags |= 65536, !1;
			}
			n = n.return;
		} while (n !== null);
		return !1;
	}
	var Oc = Error(i(461)), kc = !1;
	function Ac(e, t, n, r) {
		t.child = e === null ? oo(t, null, n, r) : ao(t, e.child, n, r);
	}
	function jc(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		if ("ref" in r) {
			var o = {};
			for (var s in r) s !== "ref" && (o[s] = r[s]);
		} else o = r;
		return ya(t), r = Jo(e, t, n, o, a, i), s = Qo(), e !== null && !kc ? ($o(e, t, i), al(e, t, i)) : (W && s && Xi(t), t.flags |= 1, Ac(e, t, r, i), t.child);
	}
	function Mc(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !ki(a) && a.defaultProps === void 0 && n.compare === null ? (t.tag = 15, t.type = a, Nc(e, t, a, r, i)) : (e = Mi(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, !ol(e, i)) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? Lr : n, n(o, r) && e.ref === t.ref) return al(e, t, i);
		}
		return t.flags |= 1, e = Ai(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function Nc(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (Lr(a, r) && e.ref === t.ref) {
				if (kc = !1, t.pendingProps = r = a, ol(e, i)) e.flags & 131072 && (kc = !0);
				else return t.lanes = e.lanes, al(e, t, i);
			}
		}
		return Vc(e, t, n, r, i);
	}
	function Pc(e, t, n, r) {
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
				return Ic(e, t, a, n, r);
			}
			if (n & 536870912) t.memoizedState = {
				baseLanes: 0,
				cachePool: null
			}, e !== null && Va(t, a === null ? null : a.cachePool), a === null ? Co() : So(t, a), ko(t);
			else return r = t.lanes = 536870912, Ic(e, t, a === null ? n : a.baseLanes | n, n, r);
		} else a === null ? (e !== null && Va(t, null), Co(), Ao()) : (Va(t, a.cachePool), So(t, a), Ao(), t.memoizedState = null);
		return Ac(e, t, i, n), t.child;
	}
	function Fc(e, t) {
		return e !== null && e.tag === 22 || t.stateNode !== null || (t.stateNode = {
			_visibility: 1,
			_pendingMarkers: null,
			_retryCache: null,
			_transitions: null
		}), t.sibling;
	}
	function Ic(e, t, n, r, i) {
		var a = Ba();
		return a = a === null ? null : {
			parent: G._currentValue,
			pool: a
		}, t.memoizedState = {
			baseLanes: n,
			cachePool: a
		}, e !== null && Va(t, null), Co(), ko(t), e !== null && _a(e, t, r, !0), t.childLanes = i, null;
	}
	function Lc(e, t) {
		return t = Xc({
			mode: t.mode,
			children: t.children
		}, e.mode), t.ref = e.ref, e.child = t, t.return = e, t;
	}
	function Rc(e, t, n) {
		return ao(t, e.child, null, n), e = Lc(t, t.pendingProps), e.flags |= 2, jo(t), t.memoizedState = null, e;
	}
	function zc(e, t, n) {
		var r = t.pendingProps, a = !!(t.flags & 128);
		if (t.flags &= -129, e === null) {
			if (W) {
				if (r.mode === "hidden") return e = Lc(t, r), t.lanes = 536870912, e.memoizedState = {
					baseLanes: 0,
					cachePool: null
				}, Fc(null, e);
				if (Oo(t), (e = $i) ? (e = am(e, ta), e = e !== null && e.data === "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Gi === null ? null : {
						id: Ki,
						overflow: qi
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = Fi(e), n.return = t, t.child = n, U = t, $i = null)) : e = null, e === null) throw ra(t);
				return t.lanes = 536870912, null;
			}
			return Lc(t, r);
		}
		var o = e.memoizedState;
		if (o !== null) {
			var s = o.dehydrated;
			if (Oo(t), a) {
				if (t.flags & 256) t.flags &= -257, t = Rc(e, t, n);
				else if (t.memoizedState !== null) t.child = e.child, t.flags |= 128, t = null;
				else throw Error(i(558));
			} else if (kc || _a(e, t, n, !1), a = (n & e.childLanes) !== 0, kc || a) {
				if (bo.current === null) {
					if (r = ed, r !== null && (s = gt(r, n), s !== 0 && s !== o.retryLane)) throw o.retryLane = s, Ci(e, s), Nd(r, e, s), Oc;
					Gd();
				}
				t = Rc(e, t, n);
			} else e = o.treeContext, $i = lm(s.nextSibling), U = t, W = !0, ea = null, ta = !1, e !== null && Qi(t, e), t = Lc(t, r), t.flags |= 134221824;
			return t;
		}
		return e = Ai(e.child, {
			mode: r.mode,
			children: r.children
		}), e.ref = t.ref, t.child = e, e.return = t, e;
	}
	function Bc(e, t) {
		var n = t.ref;
		if (n === null) e !== null && e.ref !== null && (t.flags |= 4194816);
		else {
			if (typeof n != "function" && typeof n != "object") throw Error(i(284));
			(e === null || e.ref !== n) && (t.flags |= 4194816);
		}
	}
	function Vc(e, t, n, r, i) {
		return ya(t), n = Jo(e, t, n, r, void 0, i), r = Qo(), e !== null && !kc ? ($o(e, t, i), al(e, t, i)) : (W && r && Xi(t), t.flags |= 1, Ac(e, t, n, i), t.child);
	}
	function Hc(e, t, n, r, i, a) {
		return ya(t), t.updateQueue = null, n = Xo(t, r, n, i), Yo(e), r = Qo(), e !== null && !kc ? ($o(e, t, a), al(e, t, a)) : (W && r && Xi(t), t.flags |= 1, Ac(e, t, n, a), t.child);
	}
	function Uc(e, t, n, r, i) {
		if (ya(t), t.stateNode === null) {
			var a = Ei, o = n.contextType;
			typeof o == "object" && o && (a = ba(o)), a = new n(r, a), t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, a.updater = hc, t.stateNode = a, a._reactInternals = t, a = t.stateNode, a.props = r, a.state = t.memoizedState, a.refs = {}, co(t), o = n.contextType, a.context = typeof o == "object" && o ? ba(o) : Ei, a.state = t.memoizedState, o = n.getDerivedStateFromProps, typeof o == "function" && (mc(t, n, o, r), a.state = t.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof a.getSnapshotBeforeUpdate == "function" || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (o = a.state, typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount(), o !== a.state && hc.enqueueReplaceState(a, a.state, null), _o(t, r, a, i), go(), a.state = t.memoizedState), typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !0;
		} else if (e === null) {
			a = t.stateNode;
			var s = t.memoizedProps, c = vc(n, s);
			a.props = c;
			var l = a.context, u = n.contextType;
			o = Ei, typeof u == "object" && u && (o = ba(u));
			var d = n.getDerivedStateFromProps;
			u = typeof d == "function" || typeof a.getSnapshotBeforeUpdate == "function", s = t.pendingProps !== s, u || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (s || l !== o) && _c(t, a, r, o), so = !1;
			var f = t.memoizedState;
			a.state = f, _o(t, r, a, i), go(), l = t.memoizedState, s || f !== l || so ? (typeof d == "function" && (mc(t, n, d, r), l = t.memoizedState), (c = so || gc(t, n, c, r, f, l, o)) ? (u || typeof a.UNSAFE_componentWillMount != "function" && typeof a.componentWillMount != "function" || (typeof a.componentWillMount == "function" && a.componentWillMount(), typeof a.UNSAFE_componentWillMount == "function" && a.UNSAFE_componentWillMount()), typeof a.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = l), a.props = r, a.state = l, a.context = o, r = c) : (typeof a.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			a = t.stateNode, lo(e, t), o = t.memoizedProps, u = vc(n, o), a.props = u, d = t.pendingProps, f = a.context, l = n.contextType, c = Ei, typeof l == "object" && l && (c = ba(l)), s = n.getDerivedStateFromProps, (l = typeof s == "function" || typeof a.getSnapshotBeforeUpdate == "function") || typeof a.UNSAFE_componentWillReceiveProps != "function" && typeof a.componentWillReceiveProps != "function" || (o !== d || f !== c) && _c(t, a, r, c), so = !1, f = t.memoizedState, a.state = f, _o(t, r, a, i), go();
			var p = t.memoizedState;
			o !== d || f !== p || so || e !== null && e.dependencies !== null && va(e.dependencies) ? (typeof s == "function" && (mc(t, n, s, r), p = t.memoizedState), (u = so || gc(t, n, u, r, f, p, c) || e !== null && e.dependencies !== null && va(e.dependencies)) ? (l || typeof a.UNSAFE_componentWillUpdate != "function" && typeof a.componentWillUpdate != "function" || (typeof a.componentWillUpdate == "function" && a.componentWillUpdate(r, p, c), typeof a.UNSAFE_componentWillUpdate == "function" && a.UNSAFE_componentWillUpdate(r, p, c)), typeof a.componentDidUpdate == "function" && (t.flags |= 4), typeof a.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = p), a.props = r, a.state = p, a.context = c, r = u) : (typeof a.componentDidUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof a.getSnapshotBeforeUpdate != "function" || o === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return a = r, Bc(e, t), r = !!(t.flags & 128), a || r ? (a = t.stateNode, n = r && typeof n.getDerivedStateFromError != "function" ? null : a.render(), t.flags |= 1, e !== null && r ? (t.child = ao(t, e.child, null, i), t.child = ao(t, null, n, i)) : Ac(e, t, n, i), t.memoizedState = a.state, e = t.child) : e = al(e, t, i), e;
	}
	function Wc(e, t, n, r) {
		return sa(), t.flags |= 256, Ac(e, t, n, r), t.child;
	}
	var Gc = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0,
		hydrationErrors: null
	};
	function Kc(e) {
		return {
			baseLanes: e,
			cachePool: Ha()
		};
	}
	function qc(e, t, n) {
		return e = e === null ? 0 : e.childLanes & ~n, t && (e |= dd), e;
	}
	function Jc(e, t, n) {
		var r = t.pendingProps, i = !1, a = !!(t.flags & 128), o;
		if ((o = a) || (o = e !== null && e.memoizedState === null ? !1 : !!(Mo.current & 2)), o && (i = !0, t.flags &= -129), o = !!(t.flags & 32), t.flags &= -33, e === null) {
			if (W) {
				if (i ? Do(t) : Ao(), (e = $i) ? (e = am(e, ta), e = e !== null && e.data !== "&" ? e : null, e !== null && (t.memoizedState = {
					dehydrated: e,
					treeContext: Gi === null ? null : {
						id: Ki,
						overflow: qi
					},
					retryLane: 536870912,
					hydrationErrors: null
				}, n = Fi(e), n.return = t, t.child = n, U = t, $i = null)) : e = null, e === null) throw ra(t);
				return t.lanes = sm(e) ? 32 : 536870912, null;
			}
			return a = r.children, r = r.fallback, i ? (Ao(), i = t.mode, a = Xc({
				mode: "hidden",
				children: a
			}, i), r = Ni(r, i, n, null), a.return = t, r.return = t, a.sibling = r, t.child = a, r = t.child, r.memoizedState = Kc(n), r.childLanes = qc(e, o, n), t.memoizedState = Gc, Fc(null, r)) : (Do(t), Yc(t, a));
		}
		var s = e.memoizedState;
		if (s !== null) {
			var c = s.dehydrated;
			if (c !== null) return Qc(e, t, a, o, r, c, s, n);
		}
		return i ? (Ao(), i = r.fallback, a = t.mode, s = e.child, c = s.sibling, r = Ai(s, {
			mode: "hidden",
			children: r.children
		}), r.subtreeFlags = s.subtreeFlags & 1206910976, c === null ? (i = Ni(i, a, n, null), i.flags |= 2) : i = Ai(c, i), i.return = t, r.return = t, r.sibling = i, t.child = r, Fc(null, r), r = t.child, i = e.child.memoizedState, i === null ? i = Kc(n) : (a = i.cachePool, a === null ? a = Ha() : (s = G._currentValue, a = a.parent === s ? a : {
			parent: s,
			pool: s
		}), i = {
			baseLanes: i.baseLanes | n,
			cachePool: a
		}), r.memoizedState = i, r.childLanes = qc(e, o, n), t.memoizedState = Gc, Fc(e.child, r)) : (Do(t), n = e.child, e = n.sibling, n = Ai(n, {
			mode: "visible",
			children: r.children
		}), n.return = t, n.sibling = null, e !== null && (o = t.deletions, o === null ? (t.deletions = [e], t.flags |= 16) : o.push(e)), t.child = n, t.memoizedState = null, n);
	}
	function Yc(e, t) {
		return t = Xc({
			mode: "visible",
			children: t
		}, e.mode), t.return = e, e.child = t;
	}
	function Xc(e, t) {
		return e = Oi(22, e, null, t), e.lanes = 0, e;
	}
	function Zc(e, t, n) {
		return ao(t, e.child, null, n), e = Yc(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function Qc(e, t, n, r, a, o, s, c) {
		if (n) return t.flags & 256 ? (Do(t), t.flags &= -257, Zc(e, t, c)) : t.memoizedState === null ? (Ao(), o = a.fallback, s = t.mode, a = Xc({
			mode: "visible",
			children: a.children
		}, s), o = Ni(o, s, c, null), o.flags |= 2, a.return = t, o.return = t, a.sibling = o, t.child = a, ao(t, e.child, null, c), a = t.child, a.memoizedState = Kc(c), a.childLanes = qc(e, r, c), t.memoizedState = Gc, Fc(null, a)) : (Ao(), t.child = e.child, t.flags |= 128, null);
		if (Do(t), sm(o)) {
			if (r = o.nextSibling && o.nextSibling.dataset, r) var l = r.dgst;
			return r = l, r !== "" && (a = Error(i(419)), a.stack = "", a.digest = r, la({
				value: a,
				source: null,
				stack: null
			})), Zc(e, t, c);
		}
		if (kc || _a(e, t, c, !1), r = (c & e.childLanes) !== 0, kc || r) {
			if (bo.current !== null) return Zc(e, t, c);
			if (r = ed, r !== null && (a = gt(r, c), a !== 0 && a !== s.retryLane)) throw s.retryLane = a, Ci(e, a), Nd(r, e, a), Oc;
			return om(o) || Gd(), Zc(e, t, c);
		}
		return om(o) ? (t.flags |= 192, t.child = e.child, null) : (e = s.treeContext, $i = lm(o.nextSibling), U = t, W = !0, ea = null, ta = !1, e !== null && Qi(t, e), t = Yc(t, a.children), t.flags |= 134221824, t);
	}
	function $c(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), ha(e.return, t, n);
	}
	function el(e) {
		for (var t = null; e !== null;) {
			var n = e.alternate;
			n !== null && Fo(n) === null && (t = e), e = e.sibling;
		}
		return t;
	}
	function tl(e, t, n, r, i, a) {
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
	function nl(e) {
		var t = e.child;
		for (e.child = null; t !== null;) {
			var n = t.sibling;
			t.sibling = e.child, e.child = t, t = n;
		}
	}
	function rl(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		r = r.children;
		var o = Mo.current;
		if (t.flags & 128) return No(t, o), null;
		var s = !!(o & 2);
		if (s ? (o = o & 1 | 2, t.flags |= 128) : o &= 1, No(t, o), i === "backwards" && e !== null ? (nl(e), Ac(e, t, r, n), nl(e)) : Ac(e, t, r, n), r = W ? Hi : 0, !s && e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
			if (e.tag === 13) e.memoizedState !== null && $c(e, n, t);
			else if (e.tag === 19) $c(e, n, t);
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
				n = el(t.child), n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null, nl(t)), tl(t, !0, i, null, a, r);
				break;
			case "unstable_legacy-backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && Fo(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				tl(t, !0, n, null, a, r);
				break;
			case "together":
				tl(t, !1, null, null, void 0, r);
				break;
			case "independent":
				t.memoizedState = null;
				break;
			default: n = el(t.child), n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), tl(t, !1, i, n, a, r);
		}
		return t.child;
	}
	function il(e, t, n) {
		var r = t.pendingProps;
		return pa(t, t.type, r.value), Ac(e, t, r.children, n), t.child;
	}
	function al(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), cd |= t.lanes, (n & t.childLanes) === 0) {
			if (e !== null) {
				if (_a(e, t, n, !1), (n & t.childLanes) === 0) return null;
			} else return null;
		}
		if (e !== null && t.child !== e.child) throw Error(i(153));
		if (t.child !== null) {
			for (e = t.child, n = Ai(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = Ai(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function ol(e, t) {
		return (e.lanes & t) !== 0 || (e = e.dependencies, !!(e !== null && va(e)));
	}
	function sl(e, t, n) {
		switch (t.tag) {
			case 3:
				we(t, t.stateNode.containerInfo), pa(t, G, e.memoizedState.cache), sa();
				break;
			case 27:
			case 5:
				Ee(t);
				break;
			case 4:
				we(t, t.stateNode.containerInfo);
				break;
			case 10:
				pa(t, t.type, t.memoizedProps.value);
				break;
			case 31:
				if (t.memoizedState !== null) return t.flags |= 128, Oo(t), null;
				break;
			case 13:
				var r = t.memoizedState;
				if (r !== null) {
					if (r.dehydrated !== null) return Do(t), t.flags |= 128, null;
					r = _a(e, t, n, !1);
					var i = t.child.childLanes;
					return r || (n & i) !== 0 ? Jc(e, t, n) : (Do(t), e = al(e, t, n), e === null ? null : e.sibling);
				}
				Do(t);
				break;
			case 19:
				if (t.flags & 128) return rl(e, t, n);
				if (i = !!(e.flags & 128), r = (n & t.childLanes) !== 0, r ||= (_a(e, t, n, !1), (n & t.childLanes) !== 0), i) {
					if (r) return rl(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), No(t, Mo.current), r) break;
				return null;
			case 22: return t.lanes = 0, Pc(e, t, n, t.pendingProps);
			case 24: pa(t, G, e.memoizedState.cache);
		}
		return al(e, t, n);
	}
	function cl(e, t, n) {
		if (e !== null) {
			if (e.memoizedProps !== t.pendingProps) kc = !0;
			else {
				if (!ol(e, n) && !(t.flags & 128)) return kc = !1, sl(e, t, n);
				kc = !!(e.flags & 131072);
			}
		} else kc = !1, W && t.flags & 1048576 && Yi(t, Hi, t.index);
		switch (t.lanes = 0, t.tag) {
			case 16:
				a: {
					var r = t.pendingProps;
					if (e = Ya(t.elementType), t.type = e, typeof e == "function") ki(e) ? (r = vc(e, r), t.tag = 1, t = Uc(null, t, e, r, n)) : (t.tag = 0, t = Vc(null, t, e, r, n));
					else {
						if (e != null) {
							var a = e.$$typeof;
							if (a === M) {
								t.tag = 11, t = jc(null, t, e, r, n);
								break a;
							}
							if (a === re) {
								t.tag = 14, t = Mc(null, t, e, r, n);
								break a;
							}
							if (a === te) {
								t.tag = 10, t.type = e, t = il(null, t, n);
								break a;
							}
						}
						throw t = fe(e) || e, Error(i(306, t, ""));
					}
				}
				return t;
			case 0: return Vc(e, t, t.type, t.pendingProps, n);
			case 1: return r = t.type, a = vc(r, t.pendingProps), Uc(e, t, r, a, n);
			case 3:
				a: {
					if (we(t, t.stateNode.containerInfo), e === null) throw Error(i(387));
					r = t.pendingProps;
					var o = t.memoizedState;
					a = o.element, lo(e, t), _o(t, r, null, n);
					var s = t.memoizedState;
					if (r = s.cache, pa(t, G, r), r !== o.cache && ga(t, [G], n, !0), go(), r = s.element, o.isDehydrated) {
						if (o = {
							element: r,
							isDehydrated: !1,
							cache: s.cache
						}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
							t = Wc(e, t, r, n);
							break a;
						}
						if (r !== a) {
							a = Ri(Error(i(424)), t), la(a), t = Wc(e, t, r, n);
							break a;
						}
						switch (e = t.stateNode.containerInfo, e.nodeType) {
							case 9:
								e = e.body;
								break;
							default: e = e.nodeName === "HTML" ? e.ownerDocument.body : e;
						}
						for ($i = lm(e.firstChild), U = t, W = !0, ea = null, ta = !0, n = oo(t, null, r, n), t.child = n; n;) n.flags = n.flags & -3 | 134221824, n = n.sibling;
					} else {
						if (sa(), r === a) {
							t = al(e, t, n);
							break a;
						}
						Ac(e, t, r, n);
					}
					t = t.child;
				}
				return t;
			case 26: return Bc(e, t), e === null ? (n = Nm(t.type, null, t.pendingProps, null)) ? t.memoizedState = n : W || (t.stateNode = fp(t.type, t.pendingProps, Se.current, t)) : t.memoizedState = Nm(t.type, e.memoizedProps, t.pendingProps, e.memoizedState), null;
			case 27: return Ee(t), e === null && W && (r = t.stateNode = hm(t.type, t.pendingProps, Se.current), U = t, ta = !0, a = $i, Sp(t.type) ? (um = a, $i = lm(r.firstChild)) : $i = a), Ac(e, t, t.pendingProps.children, n), Bc(e, t), e === null && (t.flags |= 4194304), t.child;
			case 5: return e === null && W && ((a = r = $i) && (r = rm(r, t.type, t.pendingProps, ta), r === null ? a = !1 : (t.stateNode = r, U = t, $i = lm(r.firstChild), ta = !1, a = !0)), a || ra(t)), Ee(t), a = t.type, o = t.pendingProps, s = e === null ? null : e.memoizedProps, r = o.children, pp(a, o) ? r = null : s !== null && pp(a, s) && (t.flags |= 32), t.memoizedState !== null && (a = Jo(e, t, Zo, null, null, n), sh._currentValue = a), Bc(e, t), Ac(e, t, r, n), t.child;
			case 6: return e === null && W && ((e = n = $i) && (n = im(n, t.pendingProps, ta), n === null ? e = !1 : (t.stateNode = n, U = t, $i = null, e = !0)), e || ra(t)), null;
			case 13: return Jc(e, t, n);
			case 4: return we(t, t.stateNode.containerInfo), r = t.pendingProps, e === null ? t.child = ao(t, null, r, n) : Ac(e, t, r, n), t.child;
			case 11: return jc(e, t, t.type, t.pendingProps, n);
			case 7: return r = t.pendingProps, Bc(e, t), Ac(e, t, r, n), t.child;
			case 8: return Ac(e, t, t.pendingProps.children, n), t.child;
			case 12: return Ac(e, t, t.pendingProps.children, n), t.child;
			case 10: return il(e, t, n);
			case 9: return a = t.type._context, r = t.pendingProps.children, ya(t), a = ba(a), r = r(a), t.flags |= 1, Ac(e, t, r, n), t.child;
			case 14: return Mc(e, t, t.type, t.pendingProps, n);
			case 15: return Nc(e, t, t.type, t.pendingProps, n);
			case 19: return rl(e, t, n);
			case 31: return zc(e, t, n);
			case 22: return Pc(e, t, n, t.pendingProps);
			case 24: return ya(t), r = ba(G), e === null ? (a = Ba(), a === null && (a = ed, o = Ea(), a.pooledCache = o, o.refCount++, o !== null && (a.pooledCacheLanes |= n), a = o), t.memoizedState = {
				parent: r,
				cache: a
			}, co(t), pa(t, G, a)) : ((e.lanes & n) !== 0 && (lo(e, t), _o(t, null, null, n), go()), a = e.memoizedState, o = t.memoizedState, a.parent === r ? (r = o.cache, pa(t, G, r), r !== a.cache && ga(t, [G], n, !0)) : (a = {
				parent: r,
				cache: r
			}, t.memoizedState = a, t.lanes === 0 && (t.memoizedState = t.updateQueue.baseState = a), pa(t, G, r))), Ac(e, t, t.pendingProps.children, n), t.child;
			case 30: return t.stateNode === null && (t.stateNode = {
				autoName: null,
				paired: null,
				clones: null,
				ref: null
			}), r = t.pendingProps, r.name != null && r.name !== "auto" ? t.flags |= e === null ? 18882560 : 18874368 : W && Xi(t), e !== null && e.memoizedProps.name !== r.name ? t.flags |= 4194816 : Bc(e, t), Ac(e, t, r.children, n), t.child;
			case 29: throw t.pendingProps;
		}
		throw Error(i(156, t.tag));
	}
	function ll(e) {
		e.flags |= 4;
	}
	function ul(e, t, n, r, i) {
		var a;
		if ((a = !!(e.mode & 32)) && (a = n === null ? Jm(t, r) : Jm(t, r) && (r.src !== n.src || r.srcSet !== n.srcSet)), a) {
			if (e.flags |= 16777216, (i & 335544128) === i) {
				if (e.stateNode.complete) e.flags |= 8192;
				else if (Hd()) e.flags |= 8192;
				else throw Xa = Ka, Wa;
			}
		} else e.flags &= -16777217;
	}
	function dl(e, t) {
		if (t.type !== "stylesheet" || t.state.loading & 4) e.flags &= -16777217;
		else if (e.flags |= 16777216, !Ym(t)) {
			if (Hd()) e.flags |= 8192;
			else throw Xa = Ka, Wa;
		}
	}
	function fl(e, t) {
		t !== null && (e.flags |= 4), e.flags & 16384 && (t = e.tag === 22 ? 536870912 : ut(), e.lanes |= t, fd |= t);
	}
	function pl(e, t) {
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
	function ml(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 1206910976, r |= i.flags & 1206910976, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function hl(e, t, n) {
		var r = t.pendingProps;
		switch (Zi(t), t.tag) {
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return ml(t), null;
			case 1: return ml(t), null;
			case 3: return n = t.stateNode, r = null, e !== null && (r = e.memoizedState.cache), t.memoizedState.cache !== r && (t.flags |= 2048), ma(G), Te(), n.pendingContext && (n.context = n.pendingContext, n.pendingContext = null), (e === null || e.child === null) && (oa(t) ? ll(t) : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, ca())), ml(t), null;
			case 26:
				var a = t.type, o = t.memoizedState;
				return e === null ? (ll(t), o === null ? (ml(t), ul(t, a, null, r, n)) : (ml(t), dl(t, o))) : o ? o === e.memoizedState ? (ml(t), t.flags &= -16777217) : (ll(t), ml(t), dl(t, o)) : (e = e.memoizedProps, e !== r && ll(t), ml(t), ul(t, a, e, r, n)), null;
			case 27:
				if (De(t), n = Se.current, a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && ll(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return ml(t), t.subtreeFlags &= -33554433, null;
					}
					e = be.current, oa(t) ? ia(t, e) : (e = hm(a, r, n), t.stateNode = e, ll(t));
				}
				return ml(t), t.subtreeFlags &= -33554433, null;
			case 5:
				if (De(t), a = t.type, e !== null && t.stateNode != null) e.memoizedProps !== r && ll(t);
				else {
					if (!r) {
						if (t.stateNode === null) throw Error(i(166));
						return ml(t), t.subtreeFlags &= -33554433, null;
					}
					if (o = be.current, oa(t)) ia(t, o);
					else {
						var s = lp(Se.current);
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
						o[St] = t, o[Ct] = r;
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
						r && ll(t);
					}
				}
				return ml(t), t.subtreeFlags &= -33554433, ul(t, t.type, e === null ? null : e.memoizedProps, t.pendingProps, n), null;
			case 6:
				if (e && t.stateNode != null) e.memoizedProps !== r && ll(t);
				else {
					if (typeof r != "string" && t.stateNode === null) throw Error(i(166));
					if (e = Se.current, oa(t)) {
						if (e = t.stateNode, n = t.memoizedProps, r = null, a = U, a !== null) switch (a.tag) {
							case 27:
							case 5: r = a.memoizedProps;
						}
						e[St] = t, e = !!(e.nodeValue === n || r !== null && !0 === r.suppressHydrationWarning || $f(e.nodeValue, n)), e || ra(t, !0);
					} else e = lp(e).createTextNode(r), e[St] = t, t.stateNode = e;
				}
				return ml(t), null;
			case 31:
				if (n = t.memoizedState, e === null || e.memoizedState !== null) {
					if (r = oa(t), n !== null) {
						if (e === null) {
							if (!r) throw Error(i(318));
							if (e = t.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(i(557));
							e[St] = t;
						} else sa(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						ml(t), e = !1;
					} else n = ca(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = n), e = !0;
					if (!e) return t.flags & 256 ? (jo(t), t) : (jo(t), null);
					if (t.flags & 128) throw Error(i(558));
				}
				return ml(t), null;
			case 13:
				if (r = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (a = oa(t), r !== null && r.dehydrated !== null) {
						if (e === null) {
							if (!a) throw Error(i(318));
							if (a = t.memoizedState, a = a === null ? null : a.dehydrated, !a) throw Error(i(317));
							a[St] = t;
						} else sa(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						ml(t), a = !1;
					} else a = ca(), e !== null && e.memoizedState !== null && (e.memoizedState.hydrationErrors = a), a = !0;
					if (!a) return t.flags & 256 ? (jo(t), t) : (jo(t), null);
				}
				return jo(t), t.flags & 128 ? (t.lanes = n, t) : (n = r !== null, e = e !== null && e.memoizedState !== null, n && (r = t.child, a = null, r.alternate !== null && r.alternate.memoizedState !== null && r.alternate.memoizedState.cachePool !== null && (a = r.alternate.memoizedState.cachePool.pool), o = null, r.memoizedState !== null && r.memoizedState.cachePool !== null && (o = r.memoizedState.cachePool.pool), o !== a && (r.flags |= 2048)), n !== e && n && (t.child.flags |= 8192), fl(t, t.updateQueue), ml(t), null);
			case 4: return Te(), e === null && Uf(t.stateNode.containerInfo), t.flags |= 67108864, ml(t), null;
			case 10: return ma(t.type), ml(t), null;
			case 19:
				if (Po(t), r = t.memoizedState, r === null) return ml(t), null;
				if (a = !!(t.flags & 128), o = r.rendering, o === null) {
					if (a) pl(r, !1);
					else {
						if (sd !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
							if (o = Fo(e), o !== null) {
								for (t.flags |= 128, pl(r, !1), e = o.updateQueue, t.updateQueue = e, fl(t, e), t.subtreeFlags = 0, e = n, n = t.child; n !== null;) ji(n, e), n = n.sibling;
								return No(t, Mo.current & 1 | 2), W && Ji(t, r.treeForkCount), t.child;
							}
							e = e.sibling;
						}
						r.tail !== null && Be() > _d && (t.flags |= 128, a = !0, pl(r, !1), t.lanes = 4194304);
					}
				} else {
					if (!a) {
						if (e = Fo(o), e !== null) {
							if (t.flags |= 128, a = !0, e = e.updateQueue, t.updateQueue = e, fl(t, e), pl(r, !0), r.tail === null && r.tailMode !== "collapsed" && r.tailMode !== "visible" && !o.alternate && !W) return ml(t), null;
						} else 2 * Be() - r.renderingStartTime > _d && n !== 536870912 && (t.flags |= 128, a = !0, pl(r, !1), t.lanes = 4194304);
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
					return r.rendering = e, r.tail = e.sibling, r.renderingStartTime = Be(), e.sibling = null, o = Mo.current, o = a ? o & 1 | 2 : o & 1, r.tailMode === "visible" || r.tailMode === "collapsed" || !n || W ? No(t, o) : (n = o, ye(To, t), ye(Mo, n), Eo === null && (Eo = t)), W && Ji(t, r.treeForkCount), e;
				}
				return ml(t), null;
			case 22:
			case 23: return jo(t), wo(), r = t.memoizedState !== null, e === null ? r && (t.flags |= 8192) : e.memoizedState !== null !== r && (t.flags |= 8192), r ? n & 536870912 && !(t.flags & 128) && (ml(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : ml(t), n = t.updateQueue, n !== null && fl(t, n.retryQueue), n = null, e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), r = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (r = t.memoizedState.cachePool.pool), r !== n && (t.flags |= 2048), e !== null && ve(za), null;
			case 24: return n = null, e !== null && (n = e.memoizedState.cache), t.memoizedState.cache !== n && (t.flags |= 2048), ma(G), ml(t), null;
			case 25: return null;
			case 30: return t.flags |= 33554432, ml(t), null;
		}
		throw Error(i(156, t.tag));
	}
	function gl(e, t) {
		switch (Zi(t), t.tag) {
			case 1: return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return ma(G), Te(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 26:
			case 27:
			case 5: return De(t), null;
			case 31:
				if (t.memoizedState !== null) {
					if (jo(t), t.alternate === null) throw Error(i(340));
					sa();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 13:
				if (jo(t), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(i(340));
					sa();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return Po(t), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, e = t.memoizedState, e !== null && (e.rendering = null, e.tail = null), t.flags |= 4, t) : null;
			case 4: return Te(), null;
			case 10: return ma(t.type), null;
			case 22:
			case 23: return jo(t), wo(), e !== null && ve(za), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 24: return ma(G), null;
			case 25: return null;
			default: return null;
		}
	}
	function _l(e, t) {
		switch (Zi(t), t.tag) {
			case 3:
				ma(G), Te();
				break;
			case 26:
			case 27:
			case 5:
				De(t);
				break;
			case 4:
				Te();
				break;
			case 31:
				t.memoizedState !== null && jo(t);
				break;
			case 13:
				jo(t);
				break;
			case 19:
				Po(t);
				break;
			case 10:
				ma(t.type);
				break;
			case 22:
			case 23:
				jo(t), wo(), e !== null && ve(za);
				break;
			case 24: ma(G);
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
			Q(t, t.return, e);
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
								Q(i, c, e);
							}
						}
					}
					r = r.next;
				} while (r !== a);
			}
		} catch (e) {
			Q(t, t.return, e);
		}
	}
	function bl(e) {
		var t = e.updateQueue;
		if (t !== null) {
			var n = e.stateNode;
			try {
				yo(t, n);
			} catch (t) {
				Q(e, e.return, t);
			}
		}
	}
	function xl(e, t, n) {
		n.props = vc(e.type, e.memoizedProps), n.state = e.memoizedState;
		try {
			n.componentWillUnmount();
		} catch (n) {
			Q(e, t, n);
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
						var i = e.stateNode, a = pi(e.memoizedProps, i);
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
			Q(e, t, n);
		}
	}
	function Cl(e, t) {
		var n = e.ref, r = e.refCleanup;
		if (n !== null) {
			if (typeof r == "function") try {
				r();
			} catch (n) {
				Q(e, t, n);
			} finally {
				e.refCleanup = null, e = e.alternate, e != null && (e.refCleanup = null);
			}
			else if (typeof n == "function") try {
				n(null);
			} catch (n) {
				Q(e, t, n);
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
			Q(e, e.return, t);
		}
	}
	function Al(e, t, n) {
		try {
			var r = e.stateNode;
			ip(r, e.type, n, t), r[Ct] = t;
		} catch (t) {
			Q(e, e.return, t);
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
		if (i === 5 || i === 6) i = e.stateNode, t ? (n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n).insertBefore(i, t) : (t = n.nodeType === 9 ? n.body : n.nodeName === "HTML" ? n.ownerDocument.body : n, t.appendChild(i), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = mn)), wl(e, r), B = !0;
		else if (i !== 4 && (i === 27 && (wl(e, r), r = null, Sp(e.type) && (n = e.stateNode, t = null)), e = e.child, e !== null)) for (Nl(e, t, n, r), e = e.sibling; e !== null;) Nl(e, t, n, r), e = e.sibling;
	}
	function Pl(e, t, n, r) {
		var i = e.tag;
		if (i === 5 || i === 6) i = e.stateNode, t ? n.insertBefore(i, t) : n.appendChild(i), wl(e, r), B = !0;
		else if (i !== 4 && (i === 27 && (wl(e, r), r = null, Sp(e.type) && (n = e.stateNode)), e = e.child, e !== null)) for (Pl(e, t, n, r), e = e.sibling; e !== null;) Pl(e, t, n, r), e = e.sibling;
	}
	function Fl(e) {
		var t = e.stateNode, n = e.memoizedProps;
		try {
			for (var r = e.type, i = t.attributes; i.length;) t.removeAttributeNode(i[0]);
			np(t, r, n), t[St] = e, t[Ct] = n;
		} catch (t) {
			Q(e, e.return, t);
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
				t = hi(t.default, t.share), t !== "none" && (Hl(e, n, t, null, !1) || Wl(e.child, !1));
			}
			e = e.sibling;
		}
	}
	function Kl(e, t) {
		if (e.tag === 30) {
			var n = e.stateNode, r = e.memoizedProps, i = pi(r, n), a = hi(r.default, n.paired ? r.share : r.enter);
			a === "none" ? Gl(e) : Hl(e, i, a, null, !1) ? (Gl(e), n.paired || t || Z(e, r.onEnter)) : Wl(e.child, !1);
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
								var a = hi(n.default, n.share);
								if (a !== "none" && (Hl(e, r, a, null, !1) ? (a = e.stateNode, i.paired = a, a.paired = i, Z(e, n.onShare)) : Wl(e.child, !1)), t.delete(r), t.size === 0) break;
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
			var t = e.memoizedProps, n = pi(t, e.stateNode), r = Ll === null ? void 0 : Ll.get(n), i = hi(t.default, r === void 0 ? t.exit : t.share);
			i !== "none" && (Hl(e, n, i, null, !1) ? r === void 0 ? Z(e, t.onExit) : (i = e.stateNode, r.paired = i, i.paired = r, Ll.delete(n), Z(e, t.onShare)) : Wl(e.child, !1)), Ll !== null && ql(e);
		} else if (e.subtreeFlags & 33554432) for (e = e.child; e !== null;) Jl(e), e = e.sibling;
		else Ll !== null && ql(e);
	}
	function Yl(e) {
		for (e = e.child; e !== null;) {
			if (e.tag === 30) {
				var t = e.memoizedProps, n = pi(t, e.stateNode);
				t = hi(t.default, t.update), e.flags &= -5, t !== "none" && Hl(e, n, t, e.memoizedState = [], !1);
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
				var n = e.memoizedProps, r = e.stateNode, i = pi(n, r), a = hi(n.default, n.update);
				if (t) {
					r = r.clones;
					var o = r === null ? null : r.map(kp);
				} else o = e.memoizedState, e.memoizedState = null;
				r = e;
				var s = e.child;
				Vl = 0, i = $l(r, s, i, i, a, o, !1), e.flags & 4 && i && (t || Z(e, n.onUpdate));
			} else e.subtreeFlags & 33554432 && eu(e, t);
			e = e.sibling;
		}
	}
	var tu = !1, nu = !1, ru = !1, iu = !1, au = typeof WeakSet == "function" ? WeakSet : Set, ou = null, su = !1, cu = !1, lu = !1, du = !1;
	function fu(e, t, n) {
		if (e = e.containerInfo, sp = gh, e = Hr(e), Wr(e)) {
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
		}, gh = !1, n = (n & 335544064) === n, ou = t, t = n ? 9270 : 1024; ou !== null;) {
			if (e = ou, n && (r = e.deletions, r !== null)) for (a = 0; a < r.length; a++) n && Jl(r[a]);
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
				r = e.child, (e.subtreeFlags & t) !== 0 && r !== null ? (r.return = e, ou = r) : (n && Yl(e), pu(n));
			}
		}
		Ll = null;
	}
	function pu(e) {
		for (; ou !== null;) {
			var t = ou, n = e, r = t.alternate, a = t.flags;
			switch (t.tag) {
				case 0:
				case 11:
				case 15: break;
				case 1:
					if (a & 1024 && r !== null) {
						n = void 0, a = r.memoizedProps, r = r.memoizedState;
						var o = t.stateNode;
						try {
							var s = vc(t.type, a);
							n = o.getSnapshotBeforeUpdate(s, r), o.__reactInternalSnapshotBeforeUpdate = n;
						} catch (e) {
							Q(t, t.return, e);
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
					n && r !== null && (n = pi(r.memoizedProps, r.stateNode), a = t.memoizedProps, a = hi(a.default, a.update), a !== "none" && Hl(r, n, a, r.memoizedState = [], !0));
					break;
				default: if (a & 1024) throw Error(i(163));
			}
			if (r = t.sibling, r !== null) {
				r.return = t.return, ou = r;
				break;
			}
			ou = t.return;
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
						Q(n, n.return, e);
					}
					else {
						var i = vc(n.type, t.memoizedProps);
						t = t.memoizedState;
						try {
							e.componentDidUpdate(i, t, e.__reactInternalSnapshotBeforeUpdate);
						} catch (e) {
							Q(n, n.return, e);
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
						yo(e, t);
					} catch (e) {
						Q(n, n.return, e);
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
					Q(e, e.return, t);
				}
				_u(e, t);
				break;
			case 6:
				try {
					e.stateNode.nodeValue = t ? "" : e.memoizedProps, B = !0;
				} catch (t) {
					Q(e, e.return, t);
				}
				break;
			case 18:
				try {
					var s = e.stateNode;
					t ? wp(s, !0) : wp(e.stateNode, !1);
				} catch (t) {
					Q(e, e.return, t);
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
		t !== null && (e.alternate = null, vu(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && At(t)), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	var yu = null, bu = !1;
	function xu(e, t, n) {
		for (n = n.child; n !== null;) Su(e, t, n), n = n.sibling;
	}
	function Su(e, t, n) {
		if (Xe && typeof Xe.onCommitFiberUnmount == "function") try {
			Xe.onCommitFiberUnmount(Ye, n);
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
						(yu.nodeType === 9 ? yu.body : yu.nodeName === "HTML" ? yu.ownerDocument.body : yu).removeChild(n.stateNode), B = !0;
					} catch (e) {
						Q(n, t, e);
					}
					else try {
						yu.removeChild(n.stateNode), B = !0;
					} catch (e) {
						Q(n, t, e);
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
				Q(t, t.return, e);
			}
		}
	}
	function wu(e, t) {
		if (t.memoizedState === null && (e = t.alternate, e !== null && (e = e.memoizedState, e !== null && (e = e.dehydrated, e !== null)))) try {
			Hh(e);
		} catch (e) {
			Q(t, t.return, e);
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
												r = a.getElementsByTagName("title")[0], (!r || r[Ot] || r[St] || r.namespaceURI === "http://www.w3.org/2000/svg" || r.hasAttribute("itemprop")) && (r = a.createElement(t), a.head.insertBefore(r, a.querySelector("head > title"))), np(r, t, n), r[St] = e, R(r), t = r;
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
										r[St] = e, R(r), t = r;
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
						on(t, ""), B = !0;
					} catch (t) {
						Q(e, e.return, t);
					}
				}
				a & 4 && e.stateNode != null && (t = e.memoizedProps, Al(e, t, r === null ? t : r.memoizedProps)), a & 1024 && (iu = !0);
				break;
			case 6:
				if (Du(t, e, n), Au(e), a & 4) {
					if (e.stateNode === null) throw Error(i(162));
					t = e.memoizedProps, n = e.stateNode;
					try {
						n.nodeValue = t, B = !0;
					} catch (t) {
						Q(e, e.return, t);
					}
				}
				break;
			case 3:
				if (B = !1, Wm = null, o = Ou, Ou = bm(t.containerInfo), Du(t, e, n), Ou = o, Au(e), a & 4 && r !== null && r.memoizedState.isDehydrated) try {
					Hh(t.containerInfo);
				} catch (t) {
					Q(e, e.return, t);
				}
				iu && (iu = !1, ju(e)), B = !1;
				break;
			case 4:
				a = ru, ru = tu, r = Ut(), o = Ou, Ou = bm(e.stateNode.containerInfo), Du(t, e, n), Au(e), Ou = o, B && cu && (lu = !0), B = r, ru = a;
				break;
			case 12:
				Du(t, e, n), Au(e);
				break;
			case 31:
				Du(t, e, n), Au(e), a & 4 && (t = e.updateQueue, t !== null && (e.updateQueue = null, Eu(e, t)));
				break;
			case 13:
				Du(t, e, n), Au(e), e.child.flags & 8192 && e.memoizedState !== null != (r !== null && r.memoizedState !== null) && (hd = Be()), a & 4 && (t = e.updateQueue, t !== null && (e.updateQueue = null, Eu(e, t)));
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
				a & 512 && (nu || r === null || Cl(r, r.return)), a = Ut(), o = cu, s = (n & 335544064) === n, c = e.memoizedProps, cu = s && hi(c.default, c.update) !== "none", Du(t, e, n), Au(e), s && r !== null && B && (e.flags |= 4), cu = o, B = a;
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
						n.flags & 32 && (on(l, ""), n.flags &= -33), Pl(e, Ml(e), l, s);
						break;
					case 3:
					case 4:
						var u = n.stateNode.containerInfo;
						Nl(e, Ml(e), u, s);
						break;
					default: throw Error(i(161));
				}
			} catch (t) {
				Q(e, e.return, t);
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
				if (du = su = !1, Bl(), Mu(t, e), !su && !lu) {
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
				r = su, su = !1, Mu(t, e), su && (lu = !0), su = r;
				break;
			case 22:
				e.memoizedState === null && (n.memoizedState === null ? Mu(t, e) : Kl(e, !1));
				break;
			case 30:
				r = su, i = Bl(), su = !1, Mu(t, e), su && (e.flags |= 4);
				var a = e.memoizedProps, o = e.stateNode;
				t = pi(a, o), o = pi(n.memoizedProps, o);
				var s = hi(a.default, a.update);
				s === "none" ? t = !1 : (a = n.memoizedState, n.memoizedState = null, n = e.child, Vl = 0, t = $l(e, n, t, o, s, a, !0), Vl !== (a === null ? 0 : a.length) && (e.flags |= 32)), e.flags & 4 && t ? (Z(e, e.memoizedProps.onUpdate), zl = i) : i !== null && (i.push.apply(i, zl), zl = i), su = e.flags & 32 ? !0 : r;
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
						Q(r, r.return, e);
					}
					if (r = a, i = r.updateQueue, i !== null) {
						var c = r.stateNode;
						try {
							var l = i.shared.hiddenCallbacks;
							if (l !== null) for (i.shared.hiddenCallbacks = null, i = 0; i < l.length; i++) vo(l[i], c);
						} catch (e) {
							Q(r, r.return, e);
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
		e !== null && e.memoizedState !== null && e.memoizedState.cachePool !== null && (n = e.memoizedState.cachePool.pool), e = null, t.memoizedState !== null && t.memoizedState.cachePool !== null && (e = t.memoizedState.cachePool.pool), e !== n && (e != null && e.refCount++, n != null && Da(n));
	}
	function Ru(e, t) {
		e = null, t.alternate !== null && (e = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== e && (t.refCount++, e != null && Da(e));
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
				zu(e, t, n, r), i && du && (e = e.containerInfo, e = e.nodeType === 9 ? e.body : e.nodeName === "HTML" ? e.ownerDocument.body : e, e.style.viewTransitionName === "root" && (e.style.viewTransitionName = ""), e = e.ownerDocument.documentElement, e !== null && e.style.viewTransitionName === "none" && (e.style.viewTransitionName = "")), a & 2048 && (a = null, t.alternate !== null && (a = t.alternate.memoizedState.cache), t = t.memoizedState.cache, t !== a && (t.refCount++, a != null && Da(a)));
				break;
			case 12:
				if (a & 2048) {
					zu(e, t, n, r), a = t.stateNode;
					try {
						var o = t.memoizedProps, s = o.id, c = o.onPostCommit;
						typeof c == "function" && c(s, t.alternate === null ? "mount" : "update", a.passiveEffectDuration, -0);
					} catch (e) {
						Q(t, t.return, e);
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
				ou = r, Xu(r, e);
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
				ou = r, Xu(r, e);
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
		for (; ou !== null;) {
			var n = ou;
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
				case 24: Da(n.memoizedState.cache);
			}
			if (r = n.child, r !== null) r.return = n, ou = r;
			else a: for (n = e; ou !== null;) {
				r = ou;
				var i = r.sibling, a = r.return;
				if (vu(r), r === n) {
					ou = null;
					break a;
				}
				if (i !== null) {
					i.return = a, ou = i;
					break a;
				}
				ou = a;
			}
		}
	}
	var Zu = {
		getCacheForType: function(e) {
			var t = ba(G), n = t.data.get(e);
			return n === void 0 && (n = e(), t.data.set(e, n)), n;
		},
		cacheSignal: function() {
			return ba(G).controller.signal;
		}
	}, Qu = typeof WeakMap == "function" ? WeakMap : Map, $u = 0, ed = null, q = null, J = 0, td = 0, nd = null, rd = !1, id = !1, ad = !1, od = 0, sd = 0, cd = 0, ld = 0, ud = 0, dd = 0, fd = 0, pd = null, md = null, Y = !1, hd = 0, gd = 0, _d = Infinity, vd = null, yd = null, bd = 0, xd = null, Sd = null, Cd = 0, wd = 0, Td = null, X = null, Ed = null, Dd = null, Od = null, kd = 0, Ad = null;
	function jd() {
		return $u & 2 && J !== 0 ? J & -J : F.T === null ? yt() : Nf();
	}
	function Md() {
		if (dd === 0) {
			if (!(J & 536870912) || W) {
				var e = rt;
				rt <<= 1, !(rt & 3932160) && (rt = 262144), dd = e;
			} else dd = 536870912;
		}
		return e = To.current, e !== null && (e.flags |= 32), dd;
	}
	function Z(e, t) {
		if (t != null) {
			var n = e.stateNode, r = n.ref;
			r === null && (r = n.ref = Pp(pi(e.memoizedProps, n))), Dd === null && (Dd = []), Dd.push(t.bind(null, r));
		}
	}
	function Nd(e, t, n) {
		(e === ed && (td === 2 || td === 9) || e.cancelPendingCommit !== null) && (Bd(e, 0), Ld(e, J, dd, !1)), ft(e, n), (!($u & 2) || e !== ed) && (e === ed && (!($u & 2) && (ld |= n), sd === 4 && Ld(e, J, dd, !1)), Tf(e));
	}
	function Pd(e, t, n) {
		if ($u & 6) throw Error(i(327));
		var r = !n && !(t & 127) && (t & e.expiredLanes) === 0 || st(e, t), a = r ? Jd(e, t) : Kd(e, t, !0), o = r;
		do {
			if (a === 0) {
				id && !r && Ld(e, t, 0, !1);
				break;
			}
			if (n = e.current.alternate, o && !Id(n)) {
				a = Kd(e, t, !1), o = !1;
				continue;
			}
			if (a === 2) {
				if (o = t, e.errorRecoveryDisabledLanes & o) var s = 0;
				else s = e.pendingLanes & -536870913, s = s === 0 ? s & 536870912 ? 536870912 : 0 : s;
				if (s !== 0) {
					t = s;
					a: {
						var c = e;
						a = pd;
						var l = c.current.memoizedState.isDehydrated;
						if (l && (Bd(c, s).flags |= 256), s = Kd(c, s, !1), s !== 2 && s !== 6) {
							if (ad && !l) {
								c.errorRecoveryDisabledLanes |= o, ld |= o, a = 4;
								break a;
							}
							o = md, md = a, o !== null && (md === null ? md = o : md.push.apply(md, o));
						}
						a = s;
					}
					if (o = !1, a !== 2) continue;
				}
			}
			if (a === 1) {
				Bd(e, 0), Ld(e, t, 0, !0);
				break;
			}
			a: {
				switch (r = e, o = a, o) {
					case 0:
					case 1: throw Error(i(345));
					case 4: if ((t & 4194048) !== t && (t & 62914560) !== t) break;
					case 6:
						Ld(r, t, dd, !rd);
						break a;
					case 2:
						md = null;
						break;
					case 3:
					case 5: break;
					default: throw Error(i(329));
				}
				if ((t & 62914560) === t && (a = hd + 300 - Be(), 10 < a)) {
					if (Ld(r, t, dd, !rd), ot(r, 0, !0) !== 0) break a;
					Cd = t, r.timeoutHandle = gp(Fd.bind(null, r, n, md, vd, Y, t, dd, ld, fd, rd, o, "Throttled", -0, 0), a);
					break a;
				}
				Fd(r, n, md, vd, Y, t, dd, ld, fd, rd, o, null, -0, 0);
			}
			break;
		} while (1);
		Tf(e);
	}
	function Fd(e, t, n, r, i, a, o, s, c, l, u, d, f, p) {
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
			unsuspend: mn
		}, Ll = null, Gu(t, a, d), h && (m = d, h = e.containerInfo, h = (h.nodeType === 9 ? h : h.ownerDocument).__reactViewTransition, h != null && (m.count++, m.waitingForViewTransition = !0, m = nh.bind(m), h.finished.then(m, m))), m = (a & 62914560) === a ? hd - Be() : (a & 4194048) === a ? gd - Be() : 0, m = eh(d, m), m !== null)) {
			Cd = a, e.cancelPendingCommit = m(tf.bind(null, e, t, a, n, r, i, o, s, c, l, u, d, null, f, p)), Ld(e, a, o, !l);
			return;
		}
		tf(e, t, a, n, r, i, o, s, c, l, u, d);
	}
	function Id(e) {
		for (var t = e;;) {
			var n = t.tag;
			if ((n === 0 || n === 11 || n === 15) && t.flags & 16384 && (n = t.updateQueue, n !== null && (n = n.stores, n !== null))) for (var r = 0; r < n.length; r++) {
				var i = n[r], a = i.getSnapshot;
				i = i.value;
				try {
					if (!Ir(a(), i)) return !1;
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
	function Ld(e, t, n, r) {
		t = ct(e, t), t &= ~ud, t &= ~ld, e.suspendedLanes |= t, e.pingedLanes &= ~t, r && (e.warmLanes |= t), r = e.expirationTimes;
		for (var i = t; 0 < i;) {
			var a = 31 - Qe(i), o = 1 << a;
			r[a] = -1, i &= ~o;
		}
		n !== 0 && mt(e, n, t);
	}
	function Rd() {
		return $u & 6 ? !0 : (Ef(0, !1), !1);
	}
	function zd() {
		if (q !== null) {
			if (td === 0) var e = q.return;
			else e = q, fa = da = null, es(e), $a = null, eo = 0, e = q;
			for (; e !== null;) _l(e.alternate, e), e = e.return;
			q = null;
		}
	}
	function Bd(e, t) {
		var n = e.timeoutHandle;
		return n !== -1 && (e.timeoutHandle = -1, _p(n)), n = e.cancelPendingCommit, n !== null && (e.cancelPendingCommit = null, n()), Cd = 0, zd(), ed = e, q = n = Ai(e.current, null), J = t, td = 0, nd = null, rd = !1, id = st(e, t), ad = !1, fd = dd = ud = ld = cd = sd = 0, md = pd = null, Y = !1, od = ct(e, t), bi(), n;
	}
	function Vd(e, t) {
		K = null, F.H = uc, t === Ua || t === Ga ? (t = Za(), td = 3) : t === Wa ? (t = Za(), td = 4) : td = t === Oc ? 8 : typeof t == "object" && t && typeof t.then == "function" ? 6 : 1, nd = t, q === null && (sd = 1, Sc(e, Ri(t, e.current)));
	}
	function Hd() {
		var e = To.current;
		return e === null ? !0 : (J & 4194048) === J ? Eo === null : (J & 62914560) === J || J & 536870912 ? e === Eo : !1;
	}
	function Ud() {
		var e = F.H;
		return F.H = uc, e === null ? uc : e;
	}
	function Wd() {
		var e = F.A;
		return F.A = Zu, e;
	}
	function Gd() {
		sd = 4, rd || (J & 4194048) !== J && To.current !== null || (id = !0), !(cd & 134217727) && !(ld & 134217727) || ed === null || Ld(ed, J, dd, !1);
	}
	function Kd(e, t, n) {
		var r = $u;
		$u |= 2;
		var i = Ud(), a = Wd();
		(ed !== e || J !== t) && (vd = null, Bd(e, t)), t = !1;
		var o = sd;
		a: do
			try {
				if (td !== 0 && q !== null) {
					var s = q, c = nd;
					switch (td) {
						case 8:
							zd(), o = 6;
							break a;
						case 3:
						case 2:
						case 9:
						case 6:
							To.current === null && (t = !0);
							var l = td;
							if (td = 0, nd = null, Qd(e, s, c, l), n && id) {
								o = 0;
								break a;
							}
							break;
						default: l = td, td = 0, nd = null, Qd(e, s, c, l);
					}
				}
				qd(), o = sd;
				break;
			} catch (t) {
				Vd(e, t);
			}
		while (1);
		return t && e.shellSuspendCounter++, fa = da = null, $u = r, F.H = i, F.A = a, q === null && (ed = null, J = 0, bi()), o;
	}
	function qd() {
		for (; q !== null;) Xd(q);
	}
	function Jd(e, t) {
		var n = $u;
		$u |= 2;
		var r = Ud(), a = Wd();
		ed !== e || J !== t ? (vd = null, _d = Be() + 500, Bd(e, t)) : id = st(e, t);
		a: do
			try {
				if (td !== 0 && q !== null) {
					t = q;
					var o = nd;
					b: switch (td) {
						case 1:
							td = 0, nd = null, Qd(e, t, o, 1);
							break;
						case 2:
						case 9:
							if (qa(o)) {
								td = 0, nd = null, Zd(t);
								break;
							}
							t = function() {
								td !== 2 && td !== 9 || ed !== e || (td = 7), Tf(e);
							}, o.then(t, t);
							break a;
						case 3:
							td = 7;
							break a;
						case 4:
							td = 5;
							break a;
						case 7:
							qa(o) ? (td = 0, nd = null, Zd(t)) : (td = 0, nd = null, Qd(e, t, o, 7));
							break;
						case 5:
							var s = null;
							switch (q.tag) {
								case 26: s = q.memoizedState;
								case 5:
								case 27:
									var c = q;
									if (s ? Ym(s) : c.stateNode.complete) {
										td = 0, nd = null;
										var l = c.sibling;
										if (l !== null) q = l;
										else {
											var u = c.return;
											u === null ? q = null : (q = u, $d(u));
										}
										break b;
									}
							}
							td = 0, nd = null, Qd(e, t, o, 5);
							break;
						case 6:
							td = 0, nd = null, Qd(e, t, o, 6);
							break;
						case 8:
							zd(), sd = 6;
							break a;
						default: throw Error(i(462));
					}
				}
				Yd();
				break;
			} catch (t) {
				Vd(e, t);
			}
		while (1);
		return fa = da = null, F.H = r, F.A = a, $u = n, q === null ? (ed = null, J = 0, bi(), sd) : 0;
	}
	function Yd() {
		for (; q !== null && !Re();) Xd(q);
	}
	function Xd(e) {
		var t = cl(e.alternate, e, od);
		e.memoizedProps = e.pendingProps, t === null ? $d(e) : q = t;
	}
	function Zd(e) {
		var t = e, n = t.alternate;
		switch (t.tag) {
			case 15:
			case 0:
				t = Hc(n, t, t.pendingProps, t.type, void 0, J);
				break;
			case 11:
				t = Hc(n, t, t.pendingProps, t.type.render, t.ref, J);
				break;
			case 5:
				es(t);
				var r = t;
				r === U && (W ? (aa(r), r.tag === 5 && r.stateNode != null && ($i = r.stateNode)) : (aa(r), W = !0));
			default: _l(n, t), t = q = ji(t, od), t = cl(n, t, od);
		}
		e.memoizedProps = e.pendingProps, t === null ? $d(e) : q = t;
	}
	function Qd(e, t, n, r) {
		fa = da = null, es(t), $a = null, eo = 0;
		var i = t.return;
		try {
			if (Dc(e, i, t, n, J)) {
				sd = 1, Sc(e, Ri(n, e.current)), q = null;
				return;
			}
		} catch (t) {
			if (i !== null) throw q = i, t;
			sd = 1, Sc(e, Ri(n, e.current)), q = null;
			return;
		}
		t.flags & 32768 ? (W || r === 1 ? e = !0 : id || J & 536870912 ? e = !1 : (rd = e = !0, (r === 2 || r === 9 || r === 3 || r === 6) && (r = To.current, r !== null && r.tag === 13 && (r.flags |= 16384))), ef(t, e)) : $d(t);
	}
	function $d(e) {
		var t = e;
		do {
			if (t.flags & 32768) {
				ef(t, rd);
				return;
			}
			e = t.return;
			var n = hl(t.alternate, t, od);
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
		sd === 0 && (sd = 5);
	}
	function ef(e, t) {
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
		sd = 6, q = null;
	}
	function tf(e, t, n, r, a, o, s, c, l, u, d, f) {
		e.cancelPendingCommit = null;
		do
			uf();
		while (bd !== 0);
		if ($u & 6) throw Error(i(327));
		if (t !== null) {
			if (t === e.current) throw Error(i(177));
			e === ed && (q = ed = null, J = 0), Sd = t, xd = e, Cd = n, Td = a, X = r, nf(e, t, n, s, c, l, f);
		}
	}
	function nf(e, t, n, r, i, a, o) {
		var s = t.lanes | t.childLanes;
		if (wd = s, s |= yi, pt(e, n, s, r, i, a), Dd = null, (n & 335544064) === n ? (Od = Aa(e), r = 10262) : (Od = null, r = 10256), (t.subtreeFlags & r) !== 0 || (t.flags & r) !== 0 ? (e.callbackNode = null, e.callbackPriority = 0, vf(We, function() {
			return df(), null;
		})) : (e.callbackNode = null, e.callbackPriority = 0), Il = !1, r = !!(t.flags & 13878), t.subtreeFlags & 13878 || r) {
			r = F.T, F.T = null, i = I.p, I.p = 2, a = $u, $u |= 4;
			try {
				fu(e, t, n);
			} finally {
				$u = a, I.p = i, F.T = r;
			}
		}
		bd = 1, Il ? Ed = Mp(o, e.containerInfo, Od, of, sf, af, cf, df, rf, null, null) : (of(), sf(), cf());
	}
	function rf(e) {
		if (bd !== 0) {
			var t = xd.onRecoverableError;
			t(e, { componentStack: null });
		}
	}
	function af() {
		bd === 3 && (bd = 0, Nu(Sd, xd), bd = 4);
	}
	function of() {
		if (bd === 1) {
			bd = 0;
			var e = xd, t = Sd, n = Cd, r = !!(t.flags & 13878);
			if (t.subtreeFlags & 13878 || r) {
				r = F.T, F.T = null;
				var i = I.p;
				I.p = 2;
				var a = $u;
				$u |= 4;
				try {
					cu = lu = !1, ku(t, e, n), n = cp;
					var o = Hr(e.containerInfo), s = n.focusedElem, c = n.selectionRange;
					if (o !== s && s && s.ownerDocument && Vr(s.ownerDocument.documentElement, s)) {
						if (c !== null && Wr(s)) {
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
					$u = a, I.p = i, F.T = r;
				}
			}
			e.current = t, bd = 2;
		}
	}
	function sf() {
		if (bd === 2) {
			bd = 0;
			var e = xd, t = Sd, n = !!(t.flags & 8772);
			if (t.subtreeFlags & 8772 || n) {
				n = F.T, F.T = null;
				var r = I.p;
				I.p = 2;
				var i = $u;
				$u |= 4;
				try {
					mu(e, t.alternate, t);
				} finally {
					$u = i, I.p = r, F.T = n;
				}
			}
			bd = 3;
		}
	}
	function cf() {
		if (bd === 4 || bd === 3) {
			bd = 0;
			var e = Ed;
			Ed = null, ze();
			var t = xd, n = Sd, r = Cd, i = X, a = (r & 335544064) === r ? 10262 : 10256;
			if ((n.subtreeFlags & a) !== 0 || (n.flags & a) !== 0 ? bd = 5 : (bd = 0, Sd = xd = null, lf(t, t.pendingLanes)), a = t.pendingLanes, a === 0 && (yd = null), vt(r), n = n.stateNode, Xe && typeof Xe.onCommitFiberRoot == "function") try {
				Xe.onCommitFiberRoot(Ye, n, void 0, (n.current.flags & 128) == 128);
			} catch {}
			if (i !== null) {
				n = F.T, a = I.p, I.p = 2, F.T = null;
				try {
					for (var o = t.onRecoverableError, s = 0; s < i.length; s++) {
						var c = i[s];
						o(c.value, { componentStack: c.stack });
					}
				} finally {
					F.T = n, I.p = a;
				}
			}
			if (i = Dd, o = Od, Od = null, i !== null && (Dd = null, o === null && (o = []), e !== null)) for (c = 0; c < i.length; c++) n = (0, i[c])(o), n !== void 0 && e.finished.finally(n);
			Cd & 3 && uf(), Tf(t), a = t.pendingLanes, r & 261930 && a & 42 ? t === Ad ? kd++ : (kd = 0, Ad = t) : (kd = 0, Ad = null), Ef(0, !1);
		}
	}
	function lf(e, t) {
		(e.pooledCacheLanes &= t) === 0 && (t = e.pooledCache, t != null && (e.pooledCache = null, Da(t)));
	}
	function uf() {
		return Ed !== null && (Ed.skipTransition(), Ed = null), of(), sf(), cf(), df();
	}
	function df() {
		if (bd !== 5) return !1;
		var e = xd, t = wd;
		wd = 0;
		var n = vt(Cd), r = F.T, a = I.p;
		try {
			I.p = 32 > n ? 32 : n, F.T = null, n = Td, Td = null;
			var o = xd, s = Cd;
			if (bd = 0, Sd = xd = null, Cd = 0, $u & 6) throw Error(i(331));
			var c = $u;
			if ($u |= 4, Ju(o.current), Bu(o, o.current, s, n), $u = c, Ef(0, !1), Xe && typeof Xe.onPostCommitFiberRoot == "function") try {
				Xe.onPostCommitFiberRoot(Ye, o);
			} catch {}
			return !0;
		} finally {
			I.p = a, F.T = r, lf(e, t);
		}
	}
	function ff(e, t, n) {
		t = Ri(n, t), t = wc(e.stateNode, t, 2), e = fo(e, t, 2), e !== null && (ft(e, 2), Tf(e));
	}
	function Q(e, t, n) {
		if (e.tag === 3) ff(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				ff(t, e, n);
				break;
			}
			if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (yd === null || !yd.has(r))) {
					e = Ri(n, e), n = Tc(2), r = fo(t, n, 2), r !== null && (Ec(n, r, t, e), ft(r, 2), Tf(r));
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
		i.has(n) || (ad = !0, i.add(n), e = mf.bind(null, e, t, n), t.then(e, e));
	}
	function mf(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), e.pingedLanes |= e.suspendedLanes & n, e.warmLanes &= ~n, ed === e && (J & n) === n && (sd === 4 || sd === 3 && (J & 62914560) === J && 300 > Be() - hd ? $u & 2 ? ud |= n : Bd(e, 0) : ud |= n, fd === J && (fd = 0)), Tf(e);
	}
	function hf(e, t) {
		t === 0 && (t = ut()), e = Ci(e, t), e !== null && (ft(e, t), Tf(e));
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
		return Ie(e, t);
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
								a = (1 << 31 - Qe(42 | e) + 1) - 1, a &= i & ~(o & ~s), a = a & 201326741 ? a & 201326741 | 1 : a ? a | 2 : 0;
							}
							a !== 0 && (n = !0, jf(r, a));
						} else a = J, a = ot(r, r === ed ? a : 0, r.cancelPendingCommit !== null || r.timeoutHandle !== -1), !(a & 3) || st(r, a) || (n = !0, jf(r, a));
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
		for (var t = Be(), n = null, r = yf; r !== null;) {
			var i = r.next, a = kf(r, t);
			a === 0 ? (r.next = null, n === null ? yf = i : n.next = i, i === null && (bf = n)) : (n = r, (e !== 0 || a & 3) && (Sf = !0)), r = i;
		}
		bd !== 0 && bd !== 5 || Ef(e, !1), wf !== 0 && (wf = 0);
	}
	function kf(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes & -62914561; 0 < a;) {
			var o = 31 - Qe(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = lt(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
		if (t = ed, n = J, n = ot(e, e === t ? n : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r = e.callbackNode, n === 0 || e === t && (td === 2 || td === 9) || e.cancelPendingCommit !== null) return r !== null && r !== null && Le(r), e.callbackNode = null, e.callbackPriority = 0;
		if (!(n & 3) || st(e, n)) {
			if (t = n & -n, t === e.callbackPriority) return t;
			switch (r !== null && Le(r), vt(n)) {
				case 2:
				case 8:
					n = Ue;
					break;
				case 32:
					n = We;
					break;
				case 268435456:
					n = Ke;
					break;
				default: n = We;
			}
			return r = Af.bind(null, e), n = Ie(n, r), e.callbackPriority = t, e.callbackNode = n, t;
		}
		return r !== null && r !== null && Le(r), e.callbackPriority = 2, e.callbackNode = null, 2;
	}
	function Af(e, t) {
		if (bd !== 0 && bd !== 5) return e.callbackNode = null, e.callbackPriority = 0, null;
		var n = e.callbackNode;
		if (uf() && e.callbackNode !== n) return null;
		var r = J;
		return r = ot(e, e === ed ? r : 0, e.cancelPendingCommit !== null || e.timeoutHandle !== -1), r === 0 ? null : (Pd(e, r, t), kf(e, Be()), e.callbackNode != null && e.callbackNode === n ? Af.bind(null, e) : null);
	}
	function jf(e, t) {
		if (uf()) return null;
		Pd(e, t, !0);
	}
	function Mf() {
		bp(function() {
			$u & 6 ? Ie(He, Df) : Of();
		});
	}
	function Nf() {
		if (wf === 0) {
			var e = Na;
			e === 0 && (e = nt, nt <<= 1, !(nt & 261888) && (nt = 256)), wf = e;
		}
		return wf;
	}
	function Pf(e) {
		return e == null || typeof e == "symbol" || typeof e == "boolean" ? null : typeof e == "function" ? e : pn(e);
	}
	function Ff(e, t, n, r, i) {
		if (t === "submit" && n && n.stateNode === i) {
			var a = Pf((i[Ct] || null).action), o = r.submitter;
			o && (t = (t = o[Ct] || null) ? Pf(t.formAction) : o.getAttribute("formAction"), t !== null && (a = t, o = null));
			var s = new Fn("action", "action", null, r, i);
			e.push({
				event: s,
				listeners: [{
					instance: null,
					listener: function() {
						if (r.defaultPrevented) {
							if (wf !== 0) {
								var e = new FormData(i, o);
								Xs(n, {
									pending: !0,
									data: e,
									method: i.method,
									action: a
								}, null, e);
							}
						} else typeof a == "function" && (s.preventDefault(), e = new FormData(i, o), Xs(n, {
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
	for (var If = 0; If < ui.length; If++) {
		var Lf = ui[If];
		di(Lf.toLowerCase(), "on" + (Lf[0].toUpperCase() + Lf.slice(1)));
	}
	di(ni, "onAnimationEnd"), di(ri, "onAnimationIteration"), di(ii, "onAnimationStart"), di("dblclick", "onDoubleClick"), di("focusin", "onFocus"), di("focusout", "onBlur"), di(ai, "onTransitionRun"), di(oi, "onTransitionStart"), di(si, "onTransitionCancel"), di(ci, "onTransitionEnd"), Rt("onMouseEnter", ["mouseout", "mouseover"]), Rt("onMouseLeave", ["mouseout", "mouseover"]), Rt("onPointerEnter", ["pointerout", "pointerover"]), Rt("onPointerLeave", ["pointerout", "pointerover"]), Lt("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), Lt("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), Lt("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), Lt("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), Lt("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), Lt("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
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
						gi(e);
					}
					i.currentTarget = null, a = c;
				}
				else for (o = 0; o < r.length; o++) {
					if (s = r[o], c = s.instance, l = s.currentTarget, s = s.listener, c !== a && i.isPropagationStopped()) break a;
					a = s, i.currentTarget = l;
					try {
						a(i);
					} catch (e) {
						gi(e);
					}
					i.currentTarget = null, a = c;
				}
			}
		}
	}
	function $(e, t) {
		var n = t[Tt];
		n === void 0 && (n = t[Tt] = /* @__PURE__ */ new Set());
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
			e[Hf] = !0, z.forEach(function(t) {
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
		n = i.bind(null, t, n, e), i = void 0, !wn || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
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
					if (s = jt(c), s === null) return;
					if (l = s.tag, l === 5 || l === 6 || l === 26 || l === 27) {
						r = a = s;
						continue a;
					}
					c = c.parentNode;
				}
			}
			r = r.return;
		}
		xn(function() {
			var r = a, i = gn(n), s = [];
			a: {
				var c = li.get(e);
				if (c !== void 0) {
					var l = Fn, u = e;
					switch (e) {
						case "keypress": if (An(n) === 0) break a;
						case "keydown":
						case "keyup":
							l = $n;
							break;
						case "focusin":
							u = "focus", l = Wn;
							break;
						case "focusout":
							u = "blur", l = Wn;
							break;
						case "beforeblur":
						case "afterblur":
							l = Wn;
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
							l = Hn;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							l = Un;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							l = nr;
							break;
						case ni:
						case ri:
						case ii:
							l = Gn;
							break;
						case ci:
							l = rr;
							break;
						case "scroll":
						case "scrollend":
							l = Ln;
							break;
						case "wheel":
							l = ir;
							break;
						case "copy":
						case "cut":
						case "paste":
							l = Kn;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup":
							l = er;
							break;
						case "submit":
							l = tr;
							break;
						case "toggle":
						case "beforetoggle": l = ar;
					}
					var d = !!(t & 4), f = !d && (e === "scroll" || e === "scrollend"), p = d ? c === null ? null : c + "Capture" : c;
					d = [];
					for (var m = r, h; m !== null;) {
						var g = m;
						if (h = g.stateNode, g = g.tag, g !== 5 && g !== 26 && g !== 27 || h === null || p === null || (g = Sn(m, p), g != null && d.push(Kf(m, g, h))), f) break;
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
					if (l = e === "mouseover" || e === "pointerover", c = e === "mouseout" || e === "pointerout", l && n !== hn && (u = n.relatedTarget || n.fromElement) && (jt(u) || u[wt])) break a;
					(c || l) && (u = i.window === i ? i : (l = i.ownerDocument) ? l.defaultView || l.parentWindow : window, c ? (l = n.relatedTarget || n.toElement, c = r, l = l ? jt(l) : null, l !== null && (f = o(l), d = l.tag, l !== f || d !== 5 && d !== 27 && d !== 6) && (l = null)) : (c = null, l = r), c !== l && (d = Hn, g = "onMouseLeave", p = "onMouseEnter", m = "mouse", (e === "pointerout" || e === "pointerover") && (d = er, g = "onPointerLeave", p = "onPointerEnter", m = "pointer"), f = c == null ? u : Nt(c), h = l == null ? u : Nt(l), u = new d(g, m + "leave", c, n, i), u.target = f, u.relatedTarget = h, g = null, jt(i) === r && (d = new d(p, m + "enter", l, n, i), d.target = h, d.relatedTarget = f, g = d), f = g, d = c && l ? w(c, l, Jf) : null, c !== null && Yf(s, u, c, d, !1), l !== null && f !== null && Yf(s, f, l, d, !0)));
				}
				a: {
					if (c = r ? Nt(r) : window, l = c.nodeName && c.nodeName.toLowerCase(), l === "select" || l === "input" && c.type === "file") var _ = wr;
					else if (vr(c)) {
						if (Tr) _ = Pr;
						else {
							_ = Mr;
							var v = jr;
						}
					} else l = c.nodeName, !l || l.toLowerCase() !== "input" || c.type !== "checkbox" && c.type !== "radio" ? r && un(r.elementType) && (_ = wr) : _ = Nr;
					if (_ &&= _(e, r)) {
						yr(s, _, n, i);
						break a;
					}
					v && v(e, c, r);
				}
				switch (v = r ? Nt(r) : window, e) {
					case "focusin":
						(vr(v) || v.contentEditable === "true") && (Kr = v, qr = r, Jr = null);
						break;
					case "focusout":
						Jr = qr = Kr = null;
						break;
					case "mousedown":
						Yr = !0;
						break;
					case "contextmenu":
					case "mouseup":
					case "dragend":
						Yr = !1, Xr(s, n, i);
						break;
					case "selectionchange": if (Gr) break;
					case "keydown":
					case "keyup": Xr(s, n, i);
				}
				var y;
				if (sr) b: {
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
				else hr ? pr(e, n) && (b = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (b = "onCompositionStart");
				b && (ur && n.locale !== "ko" && (hr || b !== "onCompositionStart" ? b === "onCompositionEnd" && hr && (y = kn()) : (En = i, Dn = "value" in En ? En.value : En.textContent, hr = !0)), v = qf(r, b), 0 < v.length && (b = new qn(b, e, null, n, i), s.push({
					event: b,
					listeners: v
				}), y ? b.data = y : (y = mr(n), y !== null && (b.data = y)))), (y = lr ? gr(e, n) : _r(e, n)) && (b = qf(r, "onBeforeInput"), 0 < b.length && (v = new qn("onBeforeInput", "beforeinput", null, n, i), s.push({
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
			if (i = i.tag, i !== 5 && i !== 26 && i !== 27 || a === null || (i = Sn(e, n), i != null && r.unshift(Kf(e, i, a)), i = Sn(e, t), i != null && r.push(Kf(e, i, a))), e.tag === 3) return r;
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
			s !== 5 && s !== 26 && s !== 27 || l === null || (c = l, i ? (l = Sn(n, a), l != null && o.unshift(Kf(n, l, c))) : i || (l = Sn(n, a), l != null && o.push(Kf(n, l, c)))), n = n.return;
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
				if (typeof r == "string") t === "body" || t === "textarea" && r === "" || on(e, r);
				else if (typeof r == "number" || typeof r == "bigint") t !== "body" && on(e, "" + r);
				else return;
				break;
			case "className":
				Gt(e, "class", r);
				break;
			case "tabIndex":
				Gt(e, "tabindex", r);
				break;
			case "dir":
			case "role":
			case "viewBox":
			case "width":
			case "height":
				Gt(e, n, r);
				break;
			case "style":
				ln(e, r, o);
				return;
			case "data": if (t !== "object") {
				Gt(e, "data", r);
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
				r = pn(r), e.setAttribute(n, r);
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
				r = pn(r), e.setAttribute(n, r);
				break;
			case "onClick":
				r != null && (e.onclick = mn);
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
				n = pn(r), e.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", n);
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
				$("beforetoggle", e), $("toggle", e), Wt(e, "popover", r);
				break;
			case "xlinkActuate":
				Kt(e, "http://www.w3.org/1999/xlink", "xlink:actuate", r);
				break;
			case "xlinkArcrole":
				Kt(e, "http://www.w3.org/1999/xlink", "xlink:arcrole", r);
				break;
			case "xlinkRole":
				Kt(e, "http://www.w3.org/1999/xlink", "xlink:role", r);
				break;
			case "xlinkShow":
				Kt(e, "http://www.w3.org/1999/xlink", "xlink:show", r);
				break;
			case "xlinkTitle":
				Kt(e, "http://www.w3.org/1999/xlink", "xlink:title", r);
				break;
			case "xlinkType":
				Kt(e, "http://www.w3.org/1999/xlink", "xlink:type", r);
				break;
			case "xmlBase":
				Kt(e, "http://www.w3.org/XML/1998/namespace", "xml:base", r);
				break;
			case "xmlLang":
				Kt(e, "http://www.w3.org/XML/1998/namespace", "xml:lang", r);
				break;
			case "xmlSpace":
				Kt(e, "http://www.w3.org/XML/1998/namespace", "xml:space", r);
				break;
			case "is":
				Wt(e, "is", r);
				break;
			case "innerText":
			case "textContent": return;
			default: if (!(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") n = dn.get(n) || n, Wt(e, n, r);
			else return;
		}
		B = !0;
	}
	function tp(e, t, n, r, a, o) {
		switch (n) {
			case "style":
				ln(e, r, o);
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
				if (typeof r == "string") on(e, r);
				else if (typeof r == "number" || typeof r == "bigint") on(e, "" + r);
				else return;
				break;
			case "onScroll":
				r != null && $("scroll", e);
				return;
			case "onScrollEnd":
				r != null && $("scrollend", e);
				return;
			case "onClick":
				r != null && (e.onclick = mn);
				return;
			case "suppressContentEditableWarning":
			case "suppressHydrationWarning":
			case "innerHTML":
			case "ref": return;
			case "innerText":
			case "textContent": return;
			default:
				if (!It.hasOwnProperty(n)) a: {
					if (n[0] === "o" && n[1] === "n" && (a = n.endsWith("Capture"), o = n.slice(2, a ? n.length - 7 : void 0), t = e[Ct] || null, t = t == null ? null : t[n], typeof t == "function" && e.removeEventListener(o, t, a), typeof r == "function")) {
						typeof t != "function" && t !== null && (n in e ? e[n] = null : e.hasAttribute(n) && e.removeAttribute(n)), e.addEventListener(o, r, a);
						break a;
					}
					B = !0, n in e ? e[n] = r : !0 === r ? e.setAttribute(n, "") : Wt(e, n, r);
				}
				return;
		}
		B = !0;
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
				en(e, o, c, l, u, s, a, !1);
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
				t = o, n = s, e.multiple = !!r, t == null ? n != null && nn(e, !!r, n, !0) : nn(e, !!r, t, !1);
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
				an(e, r, a, o);
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
			default: if (un(t)) {
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
							m !== f && (B = !0), o = m;
							break;
						case "name":
							m !== f && (B = !0), a = m;
							break;
						case "checked":
							m !== f && (B = !0), u = m;
							break;
						case "defaultChecked":
							m !== f && (B = !0), d = m;
							break;
						case "value":
							m !== f && (B = !0), s = m;
							break;
						case "defaultValue":
							m !== f && (B = !0), c = m;
							break;
						case "children":
						case "dangerouslySetInnerHTML":
							if (m != null) throw Error(i(137, t));
							break;
						default: m !== f && ep(e, t, p, m, r, f);
					}
				}
				$t(e, s, c, l, u, d, o, a);
				return;
			case "select":
				for (o in m = s = c = p = null, n) if (l = n[o], n.hasOwnProperty(o) && l != null) switch (o) {
					case "value": break;
					case "multiple": m = l;
					default: r.hasOwnProperty(o) || ep(e, t, o, null, r, l);
				}
				for (a in r) if (o = r[a], l = n[a], r.hasOwnProperty(a) && (o != null || l != null)) switch (a) {
					case "value":
						o !== l && (B = !0), p = o;
						break;
					case "defaultValue":
						o !== l && (B = !0), c = o;
						break;
					case "multiple": o !== l && (B = !0), s = o;
					default: o !== l && ep(e, t, a, o, r, l);
				}
				t = c, n = s, r = m, p == null ? !!r != !!n && (t == null ? nn(e, !!n, n ? [] : "", !1) : nn(e, !!n, t, !0)) : nn(e, !!n, p, !1);
				return;
			case "textarea":
				for (c in m = p = null, n) if (a = n[c], n.hasOwnProperty(c) && a != null && !r.hasOwnProperty(c)) switch (c) {
					case "value": break;
					case "children": break;
					default: ep(e, t, c, null, r, a);
				}
				for (s in r) if (a = r[s], o = n[s], r.hasOwnProperty(s) && (a != null || o != null)) switch (s) {
					case "value":
						a !== o && (B = !0), p = a;
						break;
					case "defaultValue":
						a !== o && (B = !0), m = a;
						break;
					case "children": break;
					case "dangerouslySetInnerHTML":
						if (a != null) throw Error(i(91));
						break;
					default: a !== o && ep(e, t, s, a, r, o);
				}
				rn(e, p, m);
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
						p !== m && (B = !0), e.selected = p && typeof p != "function" && typeof p != "symbol";
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
			default: if (un(t)) {
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
		return n = lp(n).createElement(e), n[St] = r, n[Ct] = t, np(n, e, t), R(n), n;
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
						a[Ot] || s === "SCRIPT" || s === "STYLE" || s === "LINK" && a.rel.toLowerCase() === "stylesheet" || n.removeChild(a), a = o;
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
		return _(e).addEventListener(t, n, r), !1;
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
		return _(e).removeEventListener(t, n, r), !1;
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
		t = _(t);
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
		return e.tag !== 6 && (e = _(e), pm(e, t));
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
		e !== null && (e = _(e), e = lp(e).activeElement, e !== null && f(this._fragmentFiber.child, !1, Up, e, void 0, void 0));
	};
	function Up(e, t) {
		return e.tag !== 6 && (e = _(e), e === t || e.contains(t) ? (t.blur(), !0) : !1);
	}
	Fp.prototype.observeUsing = function(e) {
		this._observers === null && (this._observers = /* @__PURE__ */ new Set()), this._observers.add(e), f(this._fragmentFiber.child, !1, Wp, e, void 0, void 0);
	};
	function Wp(e, t) {
		return e.tag !== 6 && (e = _(e), t.observe(e), !1);
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
		return e.tag !== 6 && (e = _(e), t.unobserve(e), !1);
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
		} else e = _(e), t.push.apply(t, e.getClientRects());
		return !1;
	}
	Fp.prototype.getRootNode = function(e) {
		var t = p(this._fragmentFiber);
		return t === null ? this : _(t).getRootNode(e);
	}, Fp.prototype.compareDocumentPosition = function(e) {
		var t = p(this._fragmentFiber);
		if (t === null) return Node.DOCUMENT_POSITION_DISCONNECTED;
		var n = [];
		f(this._fragmentFiber.child, !1, Hp, n, void 0, void 0);
		var r = _(t);
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
			return n === e ? i = Node.DOCUMENT_POSITION_CONTAINS : r & Node.DOCUMENT_POSITION_CONTAINED_BY && (n = h(t)[1], n === null ? i = Node.DOCUMENT_POSITION_PRECEDING : (e = _(n).compareDocumentPosition(e), i = e === 0 || e & Node.DOCUMENT_POSITION_FOLLOWING ? Node.DOCUMENT_POSITION_FOLLOWING : Node.DOCUMENT_POSITION_PRECEDING)), i |= Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC;
		}
		t = _(n[0]), i = _(n[n.length - 1]);
		var a = m(this._fragmentFiber) ? t.parentElement : r;
		if (a == null) return Node.DOCUMENT_POSITION_DISCONNECTED;
		r = a.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_CONTAINED_BY, a = a.compareDocumentPosition(i) & Node.DOCUMENT_POSITION_CONTAINED_BY;
		var o = t.compareDocumentPosition(e), s = i.compareDocumentPosition(e), c = o & Node.DOCUMENT_POSITION_CONTAINED_BY || s & Node.DOCUMENT_POSITION_CONTAINED_BY;
		return s = r && a && o & Node.DOCUMENT_POSITION_FOLLOWING && s & Node.DOCUMENT_POSITION_PRECEDING, t = r && t === e || a && i === e || c || s ? Node.DOCUMENT_POSITION_CONTAINED_BY : !r && t === e || !a && i === e ? Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC : o, t & Node.DOCUMENT_POSITION_DISCONNECTED || t & Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC || Xp(t, this._fragmentFiber, n[0], n[n.length - 1], e) ? t : Node.DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC;
	};
	function Xp(e, t, n, r, i) {
		var a = jt(i);
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
				e = _(r), Zp(e, n);
				return;
			}
			if (r = _(r), r.nodeType !== 9) {
				if (r.nodeType === 11) {
					n = "host" in r ? r.host : null, n !== null && n.scrollIntoView(e);
					return;
				}
				r.scrollIntoView(e);
			}
		}
		for (r = n ? t.length - 1 : 0; r !== (n ? -1 : t.length);) {
			var a = t[r];
			a.tag === 6 ? (a = _(a), Zp(a, n)) : _(a).scrollIntoView(e), r += n ? -1 : 1;
		}
	};
	function Qp(e, t) {
		return e = _(e), $p(e, t), !1;
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
					nm(n), At(n);
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
			} else if (!e[Ot]) switch (t) {
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
		n.dangerouslySetInnerHTML != null && (e.textContent = ""), e.onclick === mn && (e.onclick = null), At(e);
	}
	function _m(e) {
		for (var t = e.attributes; t.length;) e.removeAttributeNode(t[0]);
		At(e);
	}
	var vm = /* @__PURE__ */ new Map(), ym = /* @__PURE__ */ new Set();
	function bm(e) {
		if (typeof e.getRootNode == "function") {
			var t = e.getRootNode();
			if (t.nodeType === 9 || t.nodeType === 11) return t;
		}
		return e.nodeType === 9 ? e : e.ownerDocument;
	}
	var xm = I.d;
	I.d = {
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
		var e = xm.f(), t = Rd();
		return e || t;
	}
	function Cm(e) {
		var t = Mt(e);
		t !== null && t.tag === 5 && t.type === "form" ? Qs(t) : xm.r(e);
	}
	var wm = typeof document > "u" ? null : document;
	function Tm(e, t, n) {
		var r = wm;
		if (r && typeof t == "string" && t) {
			var i = Qt(t);
			i = "link[rel=\"" + e + "\"][href=\"" + i + "\"]", typeof n == "string" && (i += "[crossorigin=\"" + n + "\"]"), ym.has(i) || (ym.add(i), e = {
				rel: e,
				crossOrigin: n,
				href: t
			}, r.querySelector(i) === null && (t = r.createElement("link"), np(t, "link", e), R(t), r.head.appendChild(t)));
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
			var i = "link[rel=\"preload\"][as=\"" + Qt(t) + "\"]";
			t === "image" && n && n.imageSrcSet ? (i += "[imagesrcset=\"" + Qt(n.imageSrcSet) + "\"]", typeof n.imageSizes == "string" && (i += "[imagesizes=\"" + Qt(n.imageSizes) + "\"]")) : i += "[href=\"" + Qt(e) + "\"]";
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
				np(o, "link", e), t === "style" && (o[kt] = !0, o.onload = o.onerror = function() {
					Ft(o);
				}), R(o), r.head.appendChild(o);
			}
		}
	}
	function km(e, t) {
		xm.m(e, t);
		var n = wm;
		if (n && e) {
			var r = t && typeof t.as == "string" ? t.as : "script", i = "link[rel=\"modulepreload\"][as=\"" + Qt(r) + "\"][href=\"" + Qt(e) + "\"]", a = i;
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
				r = n.createElement("link"), np(r, "link", e), R(r), n.head.appendChild(r);
			}
		}
	}
	function Am(e, t, n) {
		xm.S(e, t, n);
		var r = wm;
		if (r && e) {
			var i = Pt(r).hoistableStyles, a = Pm(e);
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
					R(c), np(c, "link", e), c._p = new Promise(function(e, t) {
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
			var r = Pt(n).hoistableScripts, i = Rm(e), a = r.get(i);
			a || (a = n.querySelector(zm(i)), a || (e = T({
				src: e,
				async: !0
			}, t), (t = vm.get(i)) && Um(e, t), a = n.createElement("script"), R(a), np(a, "link", e), n.head.appendChild(a)), a = {
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
			var r = Pt(n).hoistableScripts, i = Rm(e), a = r.get(i);
			a || (a = n.querySelector(zm(i)), a || (e = T({
				src: e,
				async: !0,
				type: "module"
			}, t), (t = vm.get(i)) && Um(e, t), a = n.createElement("script"), R(a), np(a, "link", e), n.head.appendChild(a)), a = {
				type: "script",
				instance: a,
				count: 1,
				state: null
			}, r.set(i, a));
		}
	}
	function Nm(e, t, n, r) {
		var a = (a = Se.current) ? bm(a) : null;
		if (!a) throw Error(i(446));
		switch (e) {
			case "meta":
			case "title": return null;
			case "style": return typeof n.precedence == "string" && typeof n.href == "string" ? (n = Pm(n.href), t = Pt(a).hoistableStyles, r = t.get(n), r || (r = {
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
					var o = Pt(a).hoistableStyles, s = o.get(e);
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
			case "script": return t = n.async, n = n.src, typeof n == "string" && t && typeof t != "function" && typeof t != "symbol" ? (n = Rm(n), t = Pt(a).hoistableScripts, r = t.get(n), r || (r = {
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
		return "href=\"" + Qt(e) + "\"";
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
			if (!0 !== t[kt]) {
				r.loading = 1;
				return;
			}
		} else t = e.createElement("link"), t[kt] = !0, t.onload = t.onerror = Ft.bind(null, t), np(t, "link", n), R(t), e.head.appendChild(t);
		r.preload = t, t.addEventListener("load", function() {
			return r.loading |= 1;
		}), t.addEventListener("error", function() {
			return r.loading |= 2;
		});
	}
	function Rm(e) {
		return "[src=\"" + Qt(e) + "\"]";
	}
	function zm(e) {
		return "script[async]" + e;
	}
	function Bm(e, t, n) {
		if (t.count++, t.instance === null) switch (t.type) {
			case "style":
				var r = e.querySelector("style[data-href~=\"" + Qt(n.href) + "\"]");
				if (r) return t.instance = r, R(r), r;
				var a = T({}, n, {
					"data-href": n.href,
					"data-precedence": n.precedence,
					href: null,
					precedence: null
				});
				return r = (e.ownerDocument || e).createElement("style"), R(r), np(r, "style", a), Vm(r, n.precedence, e), t.instance = r;
			case "stylesheet":
				a = Pm(n.href);
				var o = e.querySelector(Fm(a));
				if (o) return t.state.loading |= 4, t.instance = o, R(o), o;
				r = Im(n), (a = vm.get(a)) && Hm(r, a), o = (e.ownerDocument || e).createElement("link"), R(o);
				var s = o;
				return s._p = new Promise(function(e, t) {
					s.onload = e, s.onerror = t;
				}), np(o, "link", r), t.state.loading |= 4, Vm(o, n.precedence, e), t.instance = o;
			case "script": return o = Rm(n.src), (a = e.querySelector(zm(o))) ? (t.instance = a, R(a), a) : (r = n, (a = vm.get(o)) && (r = T({}, n), Um(r, a)), e = e.ownerDocument || e, a = e.createElement("script"), R(a), np(a, "link", r), e.head.appendChild(a), t.instance = a);
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
			if (!(a[Ot] || a[St] || e === "link" && a.getAttribute("rel") === "stylesheet") && a.namespaceURI !== "http://www.w3.org/2000/svg") {
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
					t = a._p, typeof t == "object" && t && typeof t.then == "function" && (e.count++, e = nh.bind(e), t.then(e, e)), n.state.loading |= 4, n.instance = a, R(a);
					return;
				}
				a = t.ownerDocument || t, r = Im(r), (i = vm.get(i)) && Hm(r, i), a = a.createElement("link"), R(a);
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
		$$typeof: te,
		Provider: null,
		Consumer: null,
		_currentValue: me,
		_currentValue2: me,
		_threadCount: 0
	};
	function ch(e, t, n, r, i, a, o, s, c) {
		this.tag = 1, this.containerInfo = e, this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.next = this.pendingContext = this.context = this.cancelPendingCommit = null, this.callbackPriority = 0, this.expirationTimes = dt(-1), this.entangledLanes = this.shellSuspendCounter = this.errorRecoveryDisabledLanes = this.expiredLanes = this.warmLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = dt(0), this.hiddenUpdates = dt(null), this.identifierPrefix = r, this.onUncaughtError = i, this.onCaughtError = a, this.onRecoverableError = o, this.pooledCache = null, this.pooledCacheLanes = 0, this.formState = c, this.transitionTypes = null, this.incompleteTransitions = /* @__PURE__ */ new Map();
	}
	function lh(e, t, n, r, i, a, o, s, c, l, u, d) {
		return e = new ch(e, t, n, o, c, l, u, d, s), t = 1, !0 === a && (t |= 24), a = Oi(3, null, null, t), e.current = a, a.stateNode = e, t = Ea(), t.refCount++, e.pooledCache = t, t.refCount++, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: t
		}, co(a), e;
	}
	function uh(e) {
		return e ? (e = Ei, e) : Ei;
	}
	function dh(e, t, n, r, i, a) {
		i = uh(i), r.context === null ? r.context = i : r.pendingContext = i, r = uo(t), r.payload = { element: n }, a = a === void 0 ? null : a, a !== null && (r.callback = a), n = fo(e, r, t), n !== null && (Nd(n, e, t), po(n, e, t));
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
			var t = Ci(e, 67108864);
			t !== null && Nd(t, e, 67108864), ph(e, 67108864);
		}
	}
	function hh(e) {
		if (e.tag === 13 || e.tag === 31) {
			var t = jd();
			t = _t(t);
			var n = Ci(e, t);
			n !== null && Nd(n, e, t), ph(e, t);
		}
	}
	var gh = !0;
	function _h(e, t, n, r) {
		var i = F.T;
		F.T = null;
		var a = I.p;
		try {
			I.p = 2, yh(e, t, n, r);
		} finally {
			I.p = a, F.T = i;
		}
	}
	function vh(e, t, n, r) {
		var i = F.T;
		F.T = null;
		var a = I.p;
		try {
			I.p = 8, yh(e, t, n, r);
		} finally {
			I.p = a, F.T = i;
		}
	}
	function yh(e, t, n, r) {
		if (gh) {
			var i = bh(r);
			if (i === null) Gf(e, t, r, xh, n), Mh(e, r);
			else if (Ph(i, e, t, n, r)) r.stopPropagation();
			else if (Mh(e, r), t & 4 && -1 < jh.indexOf(e)) {
				for (; i !== null;) {
					var a = Mt(i);
					if (a !== null) switch (a.tag) {
						case 3:
							if (a = a.stateNode, a.current.memoizedState.isDehydrated) {
								var o = at(a.pendingLanes);
								if (o !== 0) {
									var s = a;
									for (s.pendingLanes |= 2, s.entangledLanes |= 2; o;) {
										var c = 1 << 31 - Qe(o);
										s.entanglements[1] |= c, o &= ~c;
									}
									Tf(a), !($u & 6) && (_d = Be() + 500, Ef(0, !1));
								}
							}
							break;
						case 31:
						case 13: s = Ci(a, 2), s !== null && Nd(s, a, 2), Rd(), ph(a, 2);
					}
					if (a = bh(r), a === null && Gf(e, t, r, xh, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else Gf(e, t, r, null, n);
		}
	}
	function bh(e) {
		return e = gn(e), Sh(e);
	}
	var xh = null;
	function Sh(e) {
		if (xh = null, e = jt(e), e !== null) {
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
			case "message": switch (Ve()) {
				case He: return 2;
				case Ue: return 8;
				case We:
				case Ge: return 32;
				case Ke: return 268435456;
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
		}, t !== null && (t = Mt(t), t !== null && mh(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
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
		var t = jt(e.target);
		if (t !== null) {
			var n = o(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = s(n), t !== null) {
						e.blockedOn = t, bt(e.priority, function() {
							hh(n);
						});
						return;
					}
				} else if (t === 31) {
					if (t = c(n), t !== null) {
						e.blockedOn = t, bt(e.priority, function() {
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
				hn = r, n.target.dispatchEvent(r), hn = null;
			} else return t = Mt(n), t !== null && mh(t), e.blockedOn = n, !1;
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
				var a = Mt(n);
				a !== null && (e.splice(t, 3), t -= 3, Xs(a, {
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
			var i = n[r], a = n[r + 1], o = i[Ct] || null;
			if (typeof a == "function") o || Vh(n);
			else if (o) {
				var s = null;
				if (a && a.hasAttribute("formAction")) {
					if (i = a, o = a[Ct] || null) s = o.formAction;
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
		dh(n, jd(), e, t, null, null);
	}, Gh.prototype.unmount = Wh.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			dh(e.current, 2, null, e, null, null), Rd(), t[wt] = null;
		}
	};
	function Gh(e) {
		this._internalRoot = e;
	}
	Gh.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = yt();
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
	I.findDOMNode = function(e) {
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(i(188)) : (e = Object.keys(e).join(","), Error(i(268, e)));
		return e = u(t), e = e === null ? null : d(e), e = e === null ? null : e.stateNode, e;
	};
	var qh = {
		bundleType: 0,
		version: "19.3.0",
		rendererPackageName: "react-dom",
		currentDispatcherRef: F,
		reconcilerVersion: "19.3.0"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var Jh = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!Jh.isDisabled && Jh.supportsFiber) try {
			Ye = Jh.inject(qh), Xe = Jh;
		} catch {}
	}
	e.createRoot = function(e, t) {
		if (!a(e)) throw Error(i(299));
		var n = !1, r = "", o = yc, s = bc, c = xc;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (r = t.identifierPrefix), t.onUncaughtError !== void 0 && (o = t.onUncaughtError), t.onCaughtError !== void 0 && (s = t.onCaughtError), t.onRecoverableError !== void 0 && (c = t.onRecoverableError)), t = lh(e, 1, !1, null, null, n, r, null, o, s, c, Uh), e[wt] = t.current, Uf(e), new Wh(t);
	};
})), fu = (/* @__PURE__ */ m(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = du();
})))(), pu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M11 11V5H13V11H19V13H13V19H11V13H5V11H11Z" })), mu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M11.9999 13.1714L16.9497 8.22168L18.3639 9.63589L11.9999 15.9999L5.63599 9.63589L7.0502 8.22168L11.9999 13.1714Z" })), hu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M16.1716 10.9999L10.8076 5.63589L12.2218 4.22168L20 11.9999L12.2218 19.778L10.8076 18.3638L16.1716 12.9999H4V10.9999H16.1716Z" })), gu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M13.1717 12.0007L8.22192 7.05093L9.63614 5.63672L16.0001 12.0007L9.63614 18.3646L8.22192 16.9504L13.1717 12.0007Z" })), _u = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M11.9997 10.5865L16.9495 5.63672L18.3637 7.05093L13.4139 12.0007L18.3637 16.9504L16.9495 18.3646L11.9997 13.4149L7.04996 18.3646L5.63574 16.9504L10.5855 12.0007L5.63574 7.05093L7.04996 5.63672L11.9997 10.5865Z" })), vu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M5 12.5C5 12.8134 5.46101 13.3584 6.53047 13.8931C7.91405 14.5849 9.87677 15 12 15C14.1232 15 16.0859 14.5849 17.4695 13.8931C18.539 13.3584 19 12.8134 19 12.5V10.3287C17.35 11.3482 14.8273 12 12 12C9.17273 12 6.64996 11.3482 5 10.3287V12.5ZM19 15.3287C17.35 16.3482 14.8273 17 12 17C9.17273 17 6.64996 16.3482 5 15.3287V17.5C5 17.8134 5.46101 18.3584 6.53047 18.8931C7.91405 19.5849 9.87677 20 12 20C14.1232 20 16.0859 19.5849 17.4695 18.8931C18.539 18.3584 19 17.8134 19 17.5V15.3287ZM3 17.5V7.5C3 5.01472 7.02944 3 12 3C16.9706 3 21 5.01472 21 7.5V17.5C21 19.9853 16.9706 22 12 22C7.02944 22 3 19.9853 3 17.5ZM12 10C14.1232 10 16.0859 9.58492 17.4695 8.89313C18.539 8.3584 19 7.81342 19 7.5C19 7.18658 18.539 6.6416 17.4695 6.10687C16.0859 5.41508 14.1232 5 12 5C9.87677 5 7.91405 5.41508 6.53047 6.10687C5.46101 6.6416 5 7.18658 5 7.5C5 7.81342 5.46101 8.3584 6.53047 8.89313C7.91405 9.58492 9.87677 10 12 10Z" })), yu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20ZM11 15H13V17H11V15ZM11 7H13V13H11V7Z" })), bu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M10 6V8H5V19H16V14H18V20C18 20.5523 17.5523 21 17 21H4C3.44772 21 3 20.5523 3 20V7C3 6.44772 3.44772 6 4 6H10ZM21 3V11H19L18.9999 6.413L11.2071 14.2071L9.79289 12.7929L17.5849 5H13V3H21Z" })), xu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM9.71002 19.6674C8.74743 17.6259 8.15732 15.3742 8.02731 13H4.06189C4.458 16.1765 6.71639 18.7747 9.71002 19.6674ZM10.0307 13C10.1811 15.4388 10.8778 17.7297 12 19.752C13.1222 17.7297 13.8189 15.4388 13.9693 13H10.0307ZM19.9381 13H15.9727C15.8427 15.3742 15.2526 17.6259 14.29 19.6674C17.2836 18.7747 19.542 16.1765 19.9381 13ZM4.06189 11H8.02731C8.15732 8.62577 8.74743 6.37407 9.71002 4.33256C6.71639 5.22533 4.458 7.8235 4.06189 11ZM10.0307 11H13.9693C13.8189 8.56122 13.1222 6.27025 12 4.24799C10.8778 6.27025 10.1811 8.56122 10.0307 11ZM14.29 4.33256C15.2526 6.37407 15.8427 8.62577 15.9727 11H19.9381C19.542 7.8235 17.2836 5.22533 14.29 4.33256Z" })), Su = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M5 14H19V4H5V14ZM5 16V20H19V16H5ZM4 2H20C20.5523 2 21 2.44772 21 3V21C21 21.5523 20.5523 22 20 22H4C3.44772 22 3 21.5523 3 21V3C3 2.44772 3.44772 2 4 2ZM15 17H17V19H15V17Z" })), Cu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12H4C4 16.4183 7.58172 20 12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C9.25022 4 6.82447 5.38734 5.38451 7.50024L8 7.5V9.5H2V3.5H4L3.99989 5.99918C5.82434 3.57075 8.72873 2 12 2ZM13 7L12.9998 11.585L16.2426 14.8284L14.8284 16.2426L10.9998 12.413L11 7H13Z" })), wu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM11 11V17H13V11H11ZM11 7V9H13V7H11Z" })), Tu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20ZM11 7H13V9H11V7ZM11 11H13V17H11V11Z" })), Eu = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M4 22C4 17.5817 7.58172 14 12 14C16.4183 14 20 17.5817 20 22H18C18 18.6863 15.3137 16 12 16C8.68629 16 6 18.6863 6 22H4ZM12 13C8.685 13 6 10.315 6 7C6 3.685 8.685 1 12 1C15.315 1 18 3.685 18 7C18 10.315 15.315 13 12 13ZM12 11C14.21 11 16 9.21 16 7C16 4.79 14.21 3 12 3C9.79 3 8 4.79 8 7C8 9.21 9.79 11 12 11Z" })), Du = ({ color: e = "currentColor", size: t = 24, className: n, ...r }) => x.createElement("svg", {
	viewBox: "0 0 24 24",
	xmlns: "http://www.w3.org/2000/svg",
	width: t,
	height: t,
	fill: e,
	...r,
	className: "remixicon " + (n || "")
}, x.createElement("path", { d: "M14 4.4375C15.3462 4.4375 16.4375 3.34619 16.4375 2H17.5625C17.5625 3.34619 18.6538 4.4375 20 4.4375V5.5625C18.6538 5.5625 17.5625 6.65381 17.5625 8H16.4375C16.4375 6.65381 15.3462 5.5625 14 5.5625V4.4375ZM1 11C4.31371 11 7 8.31371 7 5H9C9 8.31371 11.6863 11 15 11V13C11.6863 13 9 15.6863 9 19H7C7 15.6863 4.31371 13 1 13V11ZM4.87601 12C6.18717 12.7276 7.27243 13.8128 8 15.124 8.72757 13.8128 9.81283 12.7276 11.124 12 9.81283 11.2724 8.72757 10.1872 8 8.87601 7.27243 10.1872 6.18717 11.2724 4.87601 12ZM17.25 14C17.25 15.7949 15.7949 17.25 14 17.25V18.75C15.7949 18.75 17.25 20.2051 17.25 22H18.75C18.75 20.2051 20.2051 18.75 22 18.75V17.25C20.2051 17.25 18.75 15.7949 18.75 14H17.25Z" })), Ou = (e, t) => {
	let n = Array(e.length + t.length);
	for (let t = 0; t < e.length; t++) n[t] = e[t];
	for (let r = 0; r < t.length; r++) n[e.length + r] = t[r];
	return n;
}, ku = (e, t) => ({
	classGroupId: e,
	validator: t
}), Au = (e = /* @__PURE__ */ new Map(), t = null, n) => ({
	nextPart: e,
	validators: t,
	classGroupId: n
}), ju = "-", Mu = [], Nu = "arbitrary..", Pu = (e) => {
	let t = Lu(e), { conflictingClassGroups: n, conflictingClassGroupModifiers: r } = e;
	return {
		getClassGroupId: (e) => {
			if (e.startsWith("[") && e.endsWith("]")) return Iu(e);
			let n = e.split(ju);
			return Fu(n, +(n[0] === "" && n.length > 1), t);
		},
		getConflictingClassGroupIds: (e, t) => {
			if (t) {
				let t = r[e], i = n[e];
				return t ? i ? Ou(i, t) : t : i || Mu;
			}
			return n[e] || Mu;
		}
	};
}, Fu = (e, t, n) => {
	if (e.length - t === 0) return n.classGroupId;
	let r = e[t], i = n.nextPart.get(r);
	if (i) {
		let n = Fu(e, t + 1, i);
		if (n) return n;
	}
	let a = n.validators;
	if (a === null) return;
	let o = t === 0 ? e.join(ju) : e.slice(t).join(ju), s = a.length;
	for (let e = 0; e < s; e++) {
		let t = a[e];
		if (t.validator(o)) return t.classGroupId;
	}
}, Iu = (e) => e.slice(1, -1).indexOf(":") === -1 ? void 0 : (() => {
	let t = e.slice(1, -1), n = t.indexOf(":"), r = t.slice(0, n);
	return r ? Nu + r : void 0;
})(), Lu = (e) => {
	let { theme: t, classGroups: n } = e;
	return Ru(n, t);
}, Ru = (e, t) => {
	let n = Au();
	for (let r in e) {
		let i = e[r];
		zu(i, n, r, t);
	}
	return n;
}, zu = (e, t, n, r) => {
	let i = e.length;
	for (let a = 0; a < i; a++) {
		let i = e[a];
		Bu(i, t, n, r);
	}
}, Bu = (e, t, n, r) => {
	if (typeof e == "string") {
		Vu(e, t, n);
		return;
	}
	if (typeof e == "function") {
		Hu(e, t, n, r);
		return;
	}
	Uu(e, t, n, r);
}, Vu = (e, t, n) => {
	let r = e === "" ? t : Wu(t, e);
	r.classGroupId = n;
}, Hu = (e, t, n, r) => {
	if (Gu(e)) {
		zu(e(r), t, n, r);
		return;
	}
	t.validators === null && (t.validators = []), t.validators.push(ku(n, e));
}, Uu = (e, t, n, r) => {
	let i = Object.entries(e), a = i.length;
	for (let e = 0; e < a; e++) {
		let [a, o] = i[e];
		zu(o, Wu(t, a), n, r);
	}
}, Wu = (e, t) => {
	let n = e, r = t.split(ju), i = r.length;
	for (let e = 0; e < i; e++) {
		let t = r[e], i = n.nextPart.get(t);
		i || (i = Au(), n.nextPart.set(t, i)), n = i;
	}
	return n;
}, Gu = (e) => "isThemeGetter" in e && e.isThemeGetter === !0, Ku = (e) => {
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
}, qu = "!", Ju = ":", Yu = [], Xu = (e, t, n, r, i) => ({
	modifiers: e,
	hasImportantModifier: t,
	baseClassName: n,
	maybePostfixModifierPosition: r,
	isExternal: i
}), Zu = (e) => {
	let { prefix: t, experimentalParseClassName: n } = e, r = (e) => {
		let t = [], n = 0, r = 0, i = 0, a, o = e.length;
		for (let s = 0; s < o; s++) {
			let o = e[s];
			if (n === 0 && r === 0) {
				if (o === Ju) {
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
		s.endsWith(qu) ? (c = s.slice(0, -1), l = !0) : s.startsWith(qu) && (c = s.slice(1), l = !0);
		let u = a && a > i ? a - i : void 0;
		return Xu(t, l, c, u);
	};
	if (t) {
		let e = t + Ju, n = r;
		r = (t) => t.startsWith(e) ? n(t.slice(e.length)) : Xu(Yu, !1, t, void 0, !0);
	}
	if (n) {
		let e = r;
		r = (t) => n({
			className: t,
			parseClassName: e
		});
	}
	return r;
}, Qu = (e) => {
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
}, $u = (e) => ({
	cache: Ku(e.cacheSize),
	parseClassName: Zu(e),
	sortModifiers: Qu(e),
	postfixLookupClassGroupIds: ed(e),
	...Pu(e)
}), ed = (e) => {
	let t = Object.create(null), n = e.postfixLookupClassGroups;
	if (n) for (let e = 0; e < n.length; e++) t[n[e]] = !0;
	return t;
}, q = /\s+/, J = (e, t) => {
	let { parseClassName: n, getClassGroupId: r, getConflictingClassGroupIds: i, sortModifiers: a, postfixLookupClassGroupIds: o } = t, s = [], c = e.trim().split(q), l = "";
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
		let _ = d.length === 0 ? "" : d.length === 1 ? d[0] : a(d).join(":"), v = f ? _ + qu : _, y = v + g;
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
}, td = (...e) => {
	let t = 0, n, r, i = "";
	for (; t < e.length;) (n = e[t++]) && (r = nd(n)) && (i && (i += " "), i += r);
	return i;
}, nd = (e) => {
	if (typeof e == "string") return e;
	let t, n = "";
	for (let r = 0; r < e.length; r++) e[r] && (t = nd(e[r])) && (n && (n += " "), n += t);
	return n;
}, rd = (e, ...t) => {
	let n, r, i, a, o = (o) => (n = $u(t.reduce((e, t) => t(e), e())), r = n.cache.get, i = n.cache.set, a = s, s(o)), s = (e) => {
		let t = r(e);
		if (t) return t;
		let a = J(e, n);
		return i(e, a), a;
	};
	return a = o, (...e) => a(td(...e));
}, id = [], ad = (e) => {
	let t = (t) => t[e] || id;
	return t.isThemeGetter = !0, t.themeKey = e, t;
}, od = /^\[(?:(\w[\w-]*):)?(.+)\]$/i, sd = /^\((?:(\w[\w-]*):)?(.+)\)$/i, cd = /^\d+(?:\.\d+)?\/\d+(?:\.\d+)?$/, ld = /^(\d+(\.\d+)?)?(xs|sm|md|lg|xl)$/, ud = /\d+(%|px|r?em|[sdl]?v([hwib]|min|max)|pt|pc|in|cm|mm|cap|ch|ex|r?lh|cq(w|h|i|b|min|max))|\b(calc|min|max|clamp)\(.+\)|^0$/, dd = /^(rgba?|hsla?|hwb|(ok)?(lab|lch)|color-mix|color|light-dark)\(.+\)$/, fd = /^(inset_)?-?((\d+)?\.?(\d+)[a-z]+|0)_-?((\d+)?\.?(\d+)[a-z]+|0)/, pd = /^(url|image|image-set|cross-fade|element|(repeating-)?(linear|radial|conic)-gradient)\(.+\)$/, md = (e) => cd.test(e), Y = (e) => !!e && !Number.isNaN(Number(e)), hd = (e) => !!e && Number.isInteger(Number(e)), gd = (e) => e.endsWith("%") && Y(e.slice(0, -1)), _d = (e) => ld.test(e), vd = () => !0, yd = (e) => ud.test(e) && !dd.test(e), bd = () => !1, xd = (e) => fd.test(e), Sd = (e) => pd.test(e), Cd = (e) => !X(e) && !Z(e), wd = (e) => e.startsWith("@container") && (e[10] === "/" && e[11] !== void 0 || e[11] === "s" && e[16] !== void 0 && e.startsWith("-size/", 10) || e[11] === "n" && e[18] !== void 0 && e.startsWith("-normal/", 10)), Td = (e) => Bd(e, Wd, bd), X = (e) => od.test(e), Ed = (e) => Bd(e, Gd, yd), Dd = (e) => Bd(e, Kd, Y), Od = (e) => Bd(e, Jd, vd), kd = (e) => Bd(e, qd, bd), Ad = (e) => Bd(e, Hd, bd), jd = (e) => Bd(e, Ud, Sd), Md = (e) => Bd(e, Yd, xd), Z = (e) => sd.test(e), Nd = (e) => Vd(e, Gd), Pd = (e) => Vd(e, qd), Fd = (e) => Vd(e, Hd), Id = (e) => Vd(e, Wd), Ld = (e) => Vd(e, Ud), Rd = (e) => Vd(e, Yd, !0), zd = (e) => Vd(e, Jd, !0), Bd = (e, t, n) => {
	let r = od.exec(e);
	return r ? r[1] ? t(r[1]) : n(r[2]) : !1;
}, Vd = (e, t, n = !1) => {
	let r = sd.exec(e);
	return r ? r[1] ? t(r[1]) : n : !1;
}, Hd = (e) => e === "position" || e === "percentage", Ud = (e) => e === "image" || e === "url", Wd = (e) => e === "length" || e === "size" || e === "bg-size", Gd = (e) => e === "length", Kd = (e) => e === "number", qd = (e) => e === "family-name", Jd = (e) => e === "number" || e === "weight", Yd = (e) => e === "shadow", Xd = () => {
	let e = ad("color"), t = ad("font"), n = ad("text"), r = ad("font-weight"), i = ad("tracking"), a = ad("leading"), o = ad("breakpoint"), s = ad("container"), c = ad("spacing"), l = ad("radius"), u = ad("shadow"), d = ad("inset-shadow"), f = ad("text-shadow"), p = ad("drop-shadow"), m = ad("blur"), h = ad("perspective"), g = ad("aspect"), _ = ad("ease"), v = ad("animate"), y = () => [
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
		Z,
		X
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
		Z,
		X,
		c
	], T = () => [
		md,
		"full",
		"auto",
		...w()
	], E = () => [
		hd,
		"none",
		"subgrid",
		Z,
		X
	], D = () => [
		"auto",
		{ span: [
			"full",
			hd,
			Z,
			X
		] },
		hd,
		Z,
		X
	], O = () => [
		hd,
		"auto",
		Z,
		X
	], k = () => [
		"auto",
		"min",
		"max",
		"fr",
		Z,
		X
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
	], ee = () => [
		"start",
		"end",
		"center",
		"stretch",
		"center-safe",
		"end-safe"
	], j = () => ["auto", ...w()], te = () => [
		md,
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
	], M = () => [
		s,
		md,
		"screen",
		"full",
		"dvw",
		"lvw",
		"svw",
		"min",
		"max",
		"fit",
		...w()
	], ne = () => [
		md,
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
	], N = () => [
		e,
		Z,
		X
	], re = () => [
		...b(),
		Fd,
		Ad,
		{ position: [Z, X] }
	], P = () => ["no-repeat", { repeat: [
		"",
		"x",
		"y",
		"space",
		"round"
	] }], ie = () => [
		"auto",
		"cover",
		"contain",
		Id,
		Td,
		{ size: [Z, X] }
	], ae = () => [
		gd,
		Nd,
		Ed
	], oe = () => [
		"",
		"none",
		"full",
		l,
		Z,
		X
	], se = () => [
		"",
		Y,
		Nd,
		Ed
	], ce = () => [
		"solid",
		"dashed",
		"dotted",
		"double"
	], le = () => [
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
	], ue = () => [
		Y,
		gd,
		Fd,
		Ad
	], de = () => [
		"",
		"none",
		m,
		Z,
		X
	], fe = () => [
		"none",
		Y,
		Z,
		X
	], pe = () => [
		"none",
		Y,
		Z,
		X
	], F = () => [
		Y,
		Z,
		X
	], I = () => [
		md,
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
			blur: [_d],
			breakpoint: [_d],
			color: [vd],
			container: [_d],
			"drop-shadow": [_d],
			ease: [
				"in",
				"out",
				"in-out"
			],
			font: [Cd],
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
			"inset-shadow": [_d],
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
			radius: [_d],
			shadow: [_d],
			spacing: ["px", Y],
			text: [_d],
			"text-shadow": [_d],
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
				md,
				X,
				Z,
				g
			] }],
			container: ["container"],
			"container-type": [{ "@container": [
				"",
				"normal",
				"size",
				Z,
				X
			] }],
			"container-named": [wd],
			columns: [{ columns: [
				Y,
				"auto",
				X,
				Z,
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
				hd,
				"auto",
				Z,
				X
			] }],
			basis: [{ basis: [
				md,
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
				Y,
				md,
				"auto",
				"initial",
				"none",
				X
			] }],
			grow: [{ grow: [
				"",
				Y,
				Z,
				X
			] }],
			shrink: [{ shrink: [
				"",
				Y,
				Z,
				X
			] }],
			order: [{ order: [
				hd,
				"first",
				"last",
				"none",
				Z,
				X
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
			"justify-items": [{ "justify-items": [...ee(), "normal"] }],
			"justify-self": [{ "justify-self": ["auto", ...ee()] }],
			"align-content": [{ content: ["normal", ...A()] }],
			"align-items": [{ items: [...ee(), { baseline: ["", "last"] }] }],
			"align-self": [{ self: [
				"auto",
				...ee(),
				{ baseline: ["", "last"] }
			] }],
			"place-content": [{ "place-content": A() }],
			"place-items": [{ "place-items": [...ee(), "baseline"] }],
			"place-self": [{ "place-self": ["auto", ...ee()] }],
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
			m: [{ m: j() }],
			mx: [{ mx: j() }],
			my: [{ my: j() }],
			ms: [{ ms: j() }],
			me: [{ me: j() }],
			mbs: [{ mbs: j() }],
			mbe: [{ mbe: j() }],
			mt: [{ mt: j() }],
			mr: [{ mr: j() }],
			mb: [{ mb: j() }],
			ml: [{ ml: j() }],
			"space-x": [{ "space-x": w() }],
			"space-x-reverse": ["space-x-reverse"],
			"space-y": [{ "space-y": w() }],
			"space-y-reverse": ["space-y-reverse"],
			size: [{ size: te() }],
			"inline-size": [{ inline: ["auto", ...M()] }],
			"min-inline-size": [{ "min-inline": ["auto", ...M()] }],
			"max-inline-size": [{ "max-inline": ["none", ...M()] }],
			"block-size": [{ block: ["auto", ...ne()] }],
			"min-block-size": [{ "min-block": ["auto", ...ne()] }],
			"max-block-size": [{ "max-block": ["none", ...ne()] }],
			w: [{ w: [
				s,
				"screen",
				...te()
			] }],
			"min-w": [{ "min-w": [
				s,
				"screen",
				"none",
				...te()
			] }],
			"max-w": [{ "max-w": [
				s,
				"screen",
				"none",
				"prose",
				{ screen: [o] },
				...te()
			] }],
			h: [{ h: [
				"screen",
				"lh",
				...te()
			] }],
			"min-h": [{ "min-h": [
				"screen",
				"lh",
				"none",
				...te()
			] }],
			"max-h": [{ "max-h": [
				"screen",
				"lh",
				"none",
				...te()
			] }],
			"font-size": [{ text: [
				"base",
				n,
				Nd,
				Ed
			] }],
			"font-smoothing": ["antialiased", "subpixel-antialiased"],
			"font-style": ["italic", "not-italic"],
			"font-weight": [{ font: [
				r,
				zd,
				Od
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
				gd,
				X
			] }],
			"font-family": [{ font: [
				Pd,
				kd,
				t
			] }],
			"font-features": [{ "font-features": [X] }],
			"fvn-normal": ["normal-nums"],
			"fvn-ordinal": ["ordinal"],
			"fvn-slashed-zero": ["slashed-zero"],
			"fvn-figure": ["lining-nums", "oldstyle-nums"],
			"fvn-spacing": ["proportional-nums", "tabular-nums"],
			"fvn-fraction": ["diagonal-fractions", "stacked-fractions"],
			tracking: [{ tracking: [
				i,
				Z,
				X
			] }],
			"line-clamp": [{ "line-clamp": [
				Y,
				"none",
				Z,
				Dd
			] }],
			leading: [{ leading: [
				"none",
				a,
				...w()
			] }],
			"list-image": [{ "list-image": [
				"none",
				Z,
				X
			] }],
			"list-style-position": [{ list: ["inside", "outside"] }],
			"list-style-type": [{ list: [
				"disc",
				"decimal",
				"none",
				Z,
				X
			] }],
			"text-alignment": [{ text: [
				"left",
				"center",
				"right",
				"justify",
				"start",
				"end"
			] }],
			"placeholder-color": [{ placeholder: N() }],
			"text-color": [{ text: N() }],
			"text-decoration": [
				"underline",
				"overline",
				"line-through",
				"no-underline"
			],
			"text-decoration-style": [{ decoration: [...ce(), "wavy"] }],
			"text-decoration-thickness": [{ decoration: [
				Y,
				"from-font",
				"auto",
				Z,
				Ed
			] }],
			"text-decoration-color": [{ decoration: N() }],
			"underline-offset": [{ "underline-offset": [
				Y,
				"auto",
				Z,
				X
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
				hd,
				Z,
				X
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
				Z,
				X
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
				Z,
				X
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
			"bg-position": [{ bg: re() }],
			"bg-repeat": [{ bg: P() }],
			"bg-size": [{ bg: ie() }],
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
						hd,
						Z,
						X
					],
					radial: [
						"",
						Z,
						X
					],
					conic: [
						"",
						hd,
						Z,
						X
					]
				},
				Ld,
				jd
			] }],
			"bg-color": [{ bg: N() }],
			"gradient-from-pos": [{ from: ae() }],
			"gradient-via-pos": [{ via: ae() }],
			"gradient-to-pos": [{ to: ae() }],
			"gradient-from": [{ from: N() }],
			"gradient-via": [{ via: N() }],
			"gradient-to": [{ to: N() }],
			rounded: [{ rounded: oe() }],
			"rounded-s": [{ "rounded-s": oe() }],
			"rounded-e": [{ "rounded-e": oe() }],
			"rounded-t": [{ "rounded-t": oe() }],
			"rounded-r": [{ "rounded-r": oe() }],
			"rounded-b": [{ "rounded-b": oe() }],
			"rounded-l": [{ "rounded-l": oe() }],
			"rounded-ss": [{ "rounded-ss": oe() }],
			"rounded-se": [{ "rounded-se": oe() }],
			"rounded-ee": [{ "rounded-ee": oe() }],
			"rounded-es": [{ "rounded-es": oe() }],
			"rounded-tl": [{ "rounded-tl": oe() }],
			"rounded-tr": [{ "rounded-tr": oe() }],
			"rounded-br": [{ "rounded-br": oe() }],
			"rounded-bl": [{ "rounded-bl": oe() }],
			"border-w": [{ border: se() }],
			"border-w-x": [{ "border-x": se() }],
			"border-w-y": [{ "border-y": se() }],
			"border-w-s": [{ "border-s": se() }],
			"border-w-e": [{ "border-e": se() }],
			"border-w-bs": [{ "border-bs": se() }],
			"border-w-be": [{ "border-be": se() }],
			"border-w-t": [{ "border-t": se() }],
			"border-w-r": [{ "border-r": se() }],
			"border-w-b": [{ "border-b": se() }],
			"border-w-l": [{ "border-l": se() }],
			"divide-x": [{ "divide-x": se() }],
			"divide-x-reverse": ["divide-x-reverse"],
			"divide-y": [{ "divide-y": se() }],
			"divide-y-reverse": ["divide-y-reverse"],
			"border-style": [{ border: [
				...ce(),
				"hidden",
				"none"
			] }],
			"divide-style": [{ divide: [
				...ce(),
				"hidden",
				"none"
			] }],
			"border-color": [{ border: N() }],
			"border-color-x": [{ "border-x": N() }],
			"border-color-y": [{ "border-y": N() }],
			"border-color-s": [{ "border-s": N() }],
			"border-color-e": [{ "border-e": N() }],
			"border-color-bs": [{ "border-bs": N() }],
			"border-color-be": [{ "border-be": N() }],
			"border-color-t": [{ "border-t": N() }],
			"border-color-r": [{ "border-r": N() }],
			"border-color-b": [{ "border-b": N() }],
			"border-color-l": [{ "border-l": N() }],
			"divide-color": [{ divide: N() }],
			"outline-style": [{ outline: [
				...ce(),
				"none",
				"hidden"
			] }],
			"outline-offset": [{ "outline-offset": [
				Y,
				Z,
				X
			] }],
			"outline-w": [{ outline: [
				"",
				Y,
				Nd,
				Ed
			] }],
			"outline-color": [{ outline: N() }],
			shadow: [{ shadow: [
				"",
				"inner",
				"none",
				u,
				Rd,
				Md
			] }],
			"shadow-color": [{ shadow: N() }],
			"inset-shadow": [{ "inset-shadow": [
				"none",
				d,
				Rd,
				Md
			] }],
			"inset-shadow-color": [{ "inset-shadow": N() }],
			"ring-w": [{ ring: se() }],
			"ring-w-inset": ["ring-inset"],
			"ring-color": [{ ring: N() }],
			"ring-offset-w": [{ "ring-offset": [Y, Ed] }],
			"ring-offset-color": [{ "ring-offset": N() }],
			"inset-ring-w": [{ "inset-ring": se() }],
			"inset-ring-color": [{ "inset-ring": N() }],
			"text-shadow": [{ "text-shadow": [
				"none",
				f,
				Rd,
				Md
			] }],
			"text-shadow-color": [{ "text-shadow": N() }],
			opacity: [{ opacity: [
				Y,
				Z,
				X
			] }],
			"mix-blend": [{ "mix-blend": [
				...le(),
				"plus-darker",
				"plus-lighter"
			] }],
			"bg-blend": [{ "bg-blend": le() }],
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
			"mask-image-linear-pos": [{ "mask-linear": [Y] }],
			"mask-image-linear-from-pos": [{ "mask-linear-from": ue() }],
			"mask-image-linear-to-pos": [{ "mask-linear-to": ue() }],
			"mask-image-linear-from-color": [{ "mask-linear-from": N() }],
			"mask-image-linear-to-color": [{ "mask-linear-to": N() }],
			"mask-image-t-from-pos": [{ "mask-t-from": ue() }],
			"mask-image-t-to-pos": [{ "mask-t-to": ue() }],
			"mask-image-t-from-color": [{ "mask-t-from": N() }],
			"mask-image-t-to-color": [{ "mask-t-to": N() }],
			"mask-image-r-from-pos": [{ "mask-r-from": ue() }],
			"mask-image-r-to-pos": [{ "mask-r-to": ue() }],
			"mask-image-r-from-color": [{ "mask-r-from": N() }],
			"mask-image-r-to-color": [{ "mask-r-to": N() }],
			"mask-image-b-from-pos": [{ "mask-b-from": ue() }],
			"mask-image-b-to-pos": [{ "mask-b-to": ue() }],
			"mask-image-b-from-color": [{ "mask-b-from": N() }],
			"mask-image-b-to-color": [{ "mask-b-to": N() }],
			"mask-image-l-from-pos": [{ "mask-l-from": ue() }],
			"mask-image-l-to-pos": [{ "mask-l-to": ue() }],
			"mask-image-l-from-color": [{ "mask-l-from": N() }],
			"mask-image-l-to-color": [{ "mask-l-to": N() }],
			"mask-image-x-from-pos": [{ "mask-x-from": ue() }],
			"mask-image-x-to-pos": [{ "mask-x-to": ue() }],
			"mask-image-x-from-color": [{ "mask-x-from": N() }],
			"mask-image-x-to-color": [{ "mask-x-to": N() }],
			"mask-image-y-from-pos": [{ "mask-y-from": ue() }],
			"mask-image-y-to-pos": [{ "mask-y-to": ue() }],
			"mask-image-y-from-color": [{ "mask-y-from": N() }],
			"mask-image-y-to-color": [{ "mask-y-to": N() }],
			"mask-image-radial": [{ "mask-radial": [Z, X] }],
			"mask-image-radial-from-pos": [{ "mask-radial-from": ue() }],
			"mask-image-radial-to-pos": [{ "mask-radial-to": ue() }],
			"mask-image-radial-from-color": [{ "mask-radial-from": N() }],
			"mask-image-radial-to-color": [{ "mask-radial-to": N() }],
			"mask-image-radial-shape": [{ "mask-radial": ["circle", "ellipse"] }],
			"mask-image-radial-size": [{ "mask-radial": [{
				closest: ["side", "corner"],
				farthest: ["side", "corner"]
			}] }],
			"mask-image-radial-pos": [{ "mask-radial-at": b() }],
			"mask-image-conic-pos": [{ "mask-conic": [Y] }],
			"mask-image-conic-from-pos": [{ "mask-conic-from": ue() }],
			"mask-image-conic-to-pos": [{ "mask-conic-to": ue() }],
			"mask-image-conic-from-color": [{ "mask-conic-from": N() }],
			"mask-image-conic-to-color": [{ "mask-conic-to": N() }],
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
			"mask-position": [{ mask: re() }],
			"mask-repeat": [{ mask: P() }],
			"mask-size": [{ mask: ie() }],
			"mask-type": [{ "mask-type": ["alpha", "luminance"] }],
			"mask-image": [{ mask: [
				"none",
				Z,
				X
			] }],
			filter: [{ filter: [
				"",
				"none",
				Z,
				X
			] }],
			blur: [{ blur: de() }],
			brightness: [{ brightness: [
				Y,
				Z,
				X
			] }],
			contrast: [{ contrast: [
				Y,
				Z,
				X
			] }],
			"drop-shadow": [{ "drop-shadow": [
				"",
				"none",
				p,
				Rd,
				Md
			] }],
			"drop-shadow-color": [{ "drop-shadow": N() }],
			grayscale: [{ grayscale: [
				"",
				Y,
				Z,
				X
			] }],
			"hue-rotate": [{ "hue-rotate": [
				Y,
				Z,
				X
			] }],
			invert: [{ invert: [
				"",
				Y,
				Z,
				X
			] }],
			saturate: [{ saturate: [
				Y,
				Z,
				X
			] }],
			sepia: [{ sepia: [
				"",
				Y,
				Z,
				X
			] }],
			"backdrop-filter": [{ "backdrop-filter": [
				"",
				"none",
				Z,
				X
			] }],
			"backdrop-blur": [{ "backdrop-blur": de() }],
			"backdrop-brightness": [{ "backdrop-brightness": [
				Y,
				Z,
				X
			] }],
			"backdrop-contrast": [{ "backdrop-contrast": [
				Y,
				Z,
				X
			] }],
			"backdrop-grayscale": [{ "backdrop-grayscale": [
				"",
				Y,
				Z,
				X
			] }],
			"backdrop-hue-rotate": [{ "backdrop-hue-rotate": [
				Y,
				Z,
				X
			] }],
			"backdrop-invert": [{ "backdrop-invert": [
				"",
				Y,
				Z,
				X
			] }],
			"backdrop-opacity": [{ "backdrop-opacity": [
				Y,
				Z,
				X
			] }],
			"backdrop-saturate": [{ "backdrop-saturate": [
				Y,
				Z,
				X
			] }],
			"backdrop-sepia": [{ "backdrop-sepia": [
				"",
				Y,
				Z,
				X
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
				Z,
				X
			] }],
			"transition-behavior": [{ transition: ["normal", "discrete"] }],
			duration: [{ duration: [
				Y,
				"initial",
				Z,
				X
			] }],
			ease: [{ ease: [
				"linear",
				"initial",
				_,
				Z,
				X
			] }],
			delay: [{ delay: [
				Y,
				Z,
				X
			] }],
			animate: [{ animate: [
				"none",
				v,
				Z,
				X
			] }],
			backface: [{ backface: ["hidden", "visible"] }],
			perspective: [{ perspective: [
				h,
				Z,
				X
			] }],
			"perspective-origin": [{ "perspective-origin": x() }],
			rotate: [{ rotate: fe() }],
			"rotate-x": [{ "rotate-x": fe() }],
			"rotate-y": [{ "rotate-y": fe() }],
			"rotate-z": [{ "rotate-z": fe() }],
			scale: [{ scale: pe() }],
			"scale-x": [{ "scale-x": pe() }],
			"scale-y": [{ "scale-y": pe() }],
			"scale-z": [{ "scale-z": pe() }],
			"scale-3d": ["scale-3d"],
			skew: [{ skew: F() }],
			"skew-x": [{ "skew-x": F() }],
			"skew-y": [{ "skew-y": F() }],
			transform: [{ transform: [
				Z,
				X,
				"",
				"none",
				"gpu",
				"cpu"
			] }],
			"transform-origin": [{ origin: x() }],
			"transform-style": [{ transform: ["3d", "flat"] }],
			translate: [{ translate: I() }],
			"translate-x": [{ "translate-x": I() }],
			"translate-y": [{ "translate-y": I() }],
			"translate-z": [{ "translate-z": I() }],
			"translate-none": ["translate-none"],
			zoom: [{ zoom: [
				hd,
				Z,
				X
			] }],
			accent: [{ accent: N() }],
			appearance: [{ appearance: ["none", "auto"] }],
			"caret-color": [{ caret: N() }],
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
				Z,
				X
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
			"scrollbar-thumb-color": [{ "scrollbar-thumb": N() }],
			"scrollbar-track-color": [{ "scrollbar-track": N() }],
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
				Z,
				X
			] }],
			fill: [{ fill: ["none", ...N()] }],
			"stroke-w": [{ stroke: [
				Y,
				Nd,
				Ed,
				Dd
			] }],
			stroke: [{ stroke: ["none", ...N()] }],
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
}, Zd = (e, { cacheSize: t, prefix: n, experimentalParseClassName: r, extend: i = {}, override: a = {} }) => (Qd(e, "cacheSize", t), Qd(e, "prefix", n), Qd(e, "experimentalParseClassName", r), $d(e.theme, a.theme), $d(e.classGroups, a.classGroups), $d(e.conflictingClassGroups, a.conflictingClassGroups), $d(e.conflictingClassGroupModifiers, a.conflictingClassGroupModifiers), Qd(e, "postfixLookupClassGroups", a.postfixLookupClassGroups), Qd(e, "orderSensitiveModifiers", a.orderSensitiveModifiers), ef(e.theme, i.theme), ef(e.classGroups, i.classGroups), ef(e.conflictingClassGroups, i.conflictingClassGroups), ef(e.conflictingClassGroupModifiers, i.conflictingClassGroupModifiers), tf(e, i, "postfixLookupClassGroups"), tf(e, i, "orderSensitiveModifiers"), e), Qd = (e, t, n) => {
	n !== void 0 && (e[t] = n);
}, $d = (e, t) => {
	if (t) for (let n in t) Qd(e, n, t[n]);
}, ef = (e, t) => {
	if (t) for (let n in t) tf(e, t, n);
}, tf = (e, t, n) => {
	let r = t[n];
	r !== void 0 && (e[n] = e[n] ? e[n].concat(r) : r);
}, nf = (e, ...t) => typeof e == "function" ? rd(Xd, e, ...t) : rd(() => Zd(Xd(), e), ...t), rf = [
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
], af = [
	"regular",
	"medium",
	"semibold",
	"bold"
], of = nf({ extend: { classGroups: { "font-size": [{ text: rf.flatMap((e) => af.map((t) => `${e}-${t}`)) }] } } });
function sf(e) {
	return e;
}
//#endregion
//#region src/react/boardui/components/base/badges/chip.tsx
var cf = sf({
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
function lf({ variant: e = "bold", color: t = "neutral", className: n, ref: r, ...i }) {
	return /* @__PURE__ */ (0, S.jsx)("span", {
		ref: r,
		className: of(cf.base, cf.variant[e], cf.color[t], n),
		...i
	});
}
//#endregion
//#region src/api.ts
var uf = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(r(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, df = (e) => {
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
}, ff = (e) => r(e);
async function Q(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new uf(df(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function pf(e, t, n = "POST", r) {
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
	if (!i.ok) throw new uf(df(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region src/react/components/empty-state.tsx
function mf({ icon: e, title: t, children: n }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex flex-col items-center gap-2 rounded-2xl border border-separator-border px-6 py-12 text-center",
		children: [
			/* @__PURE__ */ (0, S.jsx)(e, {
				"aria-hidden": !0,
				className: "size-6 text-text-tertiary"
			}),
			/* @__PURE__ */ (0, S.jsx)("h3", {
				className: "text-headline-medium text-text-primary",
				children: t
			}),
			/* @__PURE__ */ (0, S.jsx)("p", {
				className: "max-w-prose text-body-2-regular text-text-secondary",
				children: n
			})
		]
	});
}
//#endregion
//#region src/react/components/loading-dots.tsx
function hf({ label: e }) {
	return /* @__PURE__ */ (0, S.jsxs)("p", {
		role: "status",
		className: "flex items-center gap-2 text-caption-1-regular text-text-secondary",
		children: [/* @__PURE__ */ (0, S.jsxs)("span", {
			"aria-hidden": !0,
			className: "inline-flex items-center gap-1",
			children: [
				/* @__PURE__ */ (0, S.jsx)("i", { className: "dot-wave-0 size-1 rounded-full bg-current" }),
				/* @__PURE__ */ (0, S.jsx)("i", { className: "dot-wave-1 size-1 rounded-full bg-current" }),
				/* @__PURE__ */ (0, S.jsx)("i", { className: "dot-wave-2 size-1 rounded-full bg-current" })
			]
		}), e]
	});
}
//#endregion
//#region src/react/components/note.tsx
function gf({ tone: e, title: t, extra: n, children: r }) {
	let i = /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [
		t ? /* @__PURE__ */ (0, S.jsx)("p", {
			className: "text-body-medium",
			children: t
		}) : null,
		/* @__PURE__ */ (0, S.jsx)("p", {
			className: "text-body-2-regular",
			children: r
		}),
		n
	] });
	switch (e) {
		case "info": return /* @__PURE__ */ (0, S.jsx)("div", {
			role: "status",
			className: "flex flex-col gap-0.5 rounded-2lg bg-notification-information-background px-3 py-2 text-notification-information-foreground",
			children: i
		});
		case "success": return /* @__PURE__ */ (0, S.jsx)("div", {
			role: "status",
			className: "flex flex-col gap-0.5 rounded-2lg bg-notification-success-background px-3 py-2 text-notification-success-foreground",
			children: i
		});
		case "warning": return /* @__PURE__ */ (0, S.jsx)("div", {
			role: "note",
			className: "flex flex-col gap-0.5 rounded-2lg bg-status-yellow-background px-3 py-2 text-status-yellow-text",
			children: i
		});
		case "error": return /* @__PURE__ */ (0, S.jsx)("div", {
			role: "alert",
			className: "flex flex-col gap-0.5 rounded-2lg bg-background-tertiary-error px-3 py-2 text-text-error-primary",
			children: i
		});
		default: return /* @__PURE__ */ (0, S.jsx)("div", {
			role: "note",
			className: "flex flex-col gap-0.5 rounded-2lg bg-background-tertiary-default px-3 py-2 text-text-secondary",
			children: i
		});
	}
}
//#endregion
//#region src/react/components/page.tsx
function _f({ children: e }) {
	return /* @__PURE__ */ (0, S.jsx)("div", {
		className: "mx-auto flex w-full max-w-board flex-col gap-8",
		children: e
	});
}
//#endregion
//#region src/react/components/progress.tsx
function vf({ label: e, value: t, max: n = 100, stops: r = [] }) {
	let i = Math.min(Math.max(t, 0), n);
	return /* @__PURE__ */ (0, S.jsxs)("svg", {
		role: "progressbar",
		"aria-label": e,
		"aria-valuemin": 0,
		"aria-valuemax": n,
		"aria-valuenow": t,
		viewBox: `0 0 ${n} 1`,
		preserveAspectRatio: "none",
		className: "h-1.5 w-full overflow-hidden rounded-full",
		children: [
			/* @__PURE__ */ (0, S.jsx)("rect", {
				width: n,
				height: 1,
				className: "fill-background-tertiary-default"
			}),
			/* @__PURE__ */ (0, S.jsx)("rect", {
				width: i,
				height: 1,
				className: "fill-border-focus-ring"
			}),
			r.map((e) => /* @__PURE__ */ (0, S.jsx)("rect", {
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
var yf = new Ye({ defaultOptions: { queries: {
	networkMode: "always",
	retry: 0,
	refetchOnWindowFocus: !1,
	refetchOnMount: !1,
	retryOnMount: !1
} } }), bf = "/api/tasks", xf = ["tasks"], Sf = 2e3, Cf = 1e4, wf = (e) => e?.running.length ? Sf : Cf, Tf = (e) => Q(bf, e);
async function Ef(e) {
	await yf.fetchQuery({
		queryKey: xf,
		queryFn: () => Tf(e)
	});
}
var Df = {
	manual: "手动",
	scheduled: "定时",
	startup: "启动",
	cli: "命令行"
}, Of = {
	pending: "排队中",
	running: "进行中",
	succeeded: "已完成",
	failed: "失败",
	cancelled: "已取消",
	interrupted: "被打断"
}, kf = (e) => Of[e] || e, Af = {
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
function jf(e) {
	if (typeof e != "number" || !Number.isFinite(e) || e < 0) return "";
	let t = Math.floor(e);
	if (t < 60) return `${t} 秒`;
	let n = Math.floor(t / 60);
	return n < 60 ? `${n} 分 ${t % 60} 秒` : `${Math.floor(n / 60)} 小时 ${n % 60} 分`;
}
function Mf(e) {
	if (!e) return "";
	let t = new Date(e);
	return Number.isNaN(t.getTime()) ? "" : t.toLocaleString(void 0, {
		month: "2-digit",
		day: "2-digit",
		hour: "2-digit",
		minute: "2-digit"
	});
}
function Nf(e) {
	return Object.entries(e || {}).filter(([e, t]) => e !== "blocked_by" && (typeof t == "number" || typeof t == "string") && String(t) !== "").map(([e, t]) => `${Af[e] || e} ${t}`).join(" · ");
}
//#endregion
//#region src/react/activity/activity-page.tsx
var Pf = {
	succeeded: "lime",
	failed: "rose",
	cancelled: "yellow",
	interrupted: "yellow"
};
function Ff({ status: e }) {
	return /* @__PURE__ */ (0, S.jsx)(lf, {
		color: Pf[e] ?? "neutral",
		children: kf(e)
	});
}
function If({ run: e, meta: t, children: n, footer: r }) {
	return /* @__PURE__ */ (0, S.jsxs)("li", {
		"data-status": e.status,
		"data-task-key": e.task_key,
		className: e.status === "failed" ? "flex flex-col rounded-2xl border border-border-error-default" : "flex flex-col rounded-2xl border border-separator-border",
		children: [/* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex flex-col gap-1.5 px-5 pt-5 pb-4",
			children: [
				/* @__PURE__ */ (0, S.jsxs)("div", {
					className: "flex flex-wrap items-center gap-2",
					children: [/* @__PURE__ */ (0, S.jsx)("strong", {
						className: "min-w-0 break-words text-title-1-medium text-text-primary",
						children: e.task_label
					}), /* @__PURE__ */ (0, S.jsx)(Ff, { status: e.status })]
				}),
				/* @__PURE__ */ (0, S.jsx)("p", {
					className: "text-caption-1-regular text-text-secondary",
					children: t
				}),
				n
			]
		}), r ? /* @__PURE__ */ (0, S.jsx)("div", {
			className: "border-t border-separator-border px-5 py-3",
			children: /* @__PURE__ */ (0, S.jsx)("p", {
				className: "text-caption-1-regular text-text-secondary",
				children: r
			})
		}) : null]
	});
}
function Lf({ run: e }) {
	let t = e.progress_total || 0, n = e.progress_current || 0, r = e.progress_label || "正在进行", i = jf(e.elapsed_seconds), a = [Df[e.trigger] || e.trigger, i && `已跑 ${i}`].filter(Boolean).join(" · ");
	return /* @__PURE__ */ (0, S.jsx)(If, {
		run: e,
		meta: a,
		children: t > 0 ? /* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex flex-col gap-1.5",
			children: [/* @__PURE__ */ (0, S.jsx)(vf, {
				label: r,
				value: n,
				max: t
			}), /* @__PURE__ */ (0, S.jsxs)("p", {
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
		}) : /* @__PURE__ */ (0, S.jsx)(hf, { label: r })
	});
}
function Rf({ run: e }) {
	let t = Nf(e.result_summary), n = jf(e.elapsed_seconds), r = [
		Df[e.trigger] || e.trigger,
		Mf(e.finished_at),
		n && `用时 ${n}`
	].filter(Boolean).join(" · ");
	return /* @__PURE__ */ (0, S.jsx)(If, {
		run: e,
		meta: r,
		footer: e.error,
		children: t ? /* @__PURE__ */ (0, S.jsx)("p", {
			className: "text-caption-1-regular text-text-secondary",
			children: t
		}) : null
	});
}
function zf({ title: e, children: t }) {
	let n = (0, x.useId)();
	return /* @__PURE__ */ (0, S.jsxs)("section", {
		"aria-labelledby": n,
		className: "flex min-w-0 flex-col gap-3",
		children: [/* @__PURE__ */ (0, S.jsx)("h3", {
			id: n,
			className: "text-title-2-semibold text-text-primary",
			children: e
		}), t]
	});
}
function Bf({ live: e = !1, children: t }) {
	return /* @__PURE__ */ (0, S.jsx)("ul", {
		"aria-live": e ? "polite" : void 0,
		className: "flex min-w-0 flex-col gap-3",
		children: t
	});
}
function $(e) {
	let t = ct({
		queryKey: xf,
		queryFn: ({ signal: e }) => Tf(e),
		refetchInterval: (e) => wf(e.state.data)
	}), n = t.data, r = t.error ? ff(t.error) : "";
	if (!n) return /* @__PURE__ */ (0, S.jsx)(_f, { children: /* @__PURE__ */ (0, S.jsx)(gf, {
		tone: "error",
		children: r || "读取任务中心失败"
	}) });
	let i = n.running || [], a = n.skipped || [], o = (n.finished || []).filter((e) => !a.some((t) => t.id === e.id)), s = !i.length && !a.length && !o.length;
	return /* @__PURE__ */ (0, S.jsxs)(_f, { children: [
		r ? /* @__PURE__ */ (0, S.jsx)(gf, {
			tone: "error",
			children: r
		}) : null,
		n.available === !1 ? /* @__PURE__ */ (0, S.jsx)(gf, {
			tone: "warning",
			children: n.message || "账本上还没有任务中心的表"
		}) : null,
		s ? /* @__PURE__ */ (0, S.jsx)(mf, {
			icon: Cu,
			title: "还没有任务记录",
			children: "扫描、追更检查、批量操作和命令行批处理跑起来之后，这里会显示它们的进度与结果。"
		}) : /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [
			/* @__PURE__ */ (0, S.jsx)(zf, {
				title: "正在进行",
				children: i.length ? /* @__PURE__ */ (0, S.jsx)(Bf, {
					live: !0,
					children: i.map((e) => /* @__PURE__ */ (0, S.jsx)(Lf, { run: e }, e.id))
				}) : /* @__PURE__ */ (0, S.jsx)("p", {
					className: "text-body-2-regular text-text-secondary",
					children: "没有任务在跑。"
				})
			}),
			a.length ? /* @__PURE__ */ (0, S.jsx)(zf, {
				title: "被挡下的",
				children: /* @__PURE__ */ (0, S.jsx)(Bf, { children: a.map((e) => /* @__PURE__ */ (0, S.jsx)(Rf, { run: e }, e.id)) })
			}) : null,
			o.length ? /* @__PURE__ */ (0, S.jsx)(zf, {
				title: "最近完成",
				children: /* @__PURE__ */ (0, S.jsx)(Bf, { children: o.map((e) => /* @__PURE__ */ (0, S.jsx)(Rf, { run: e }, e.id)) })
			}) : null
		] })
	] });
}
//#endregion
//#region node_modules/react-aria-components/dist/private/utils.mjs
var Vf = Symbol("default");
function Hf({ values: e, children: t }) {
	for (let [n, r] of e) t = /*#__PURE__*/ x.createElement(n.Provider, { value: r }, t);
	return t;
}
function Uf(e) {
	let { className: t, style: n, children: r, defaultClassName: i, defaultChildren: a, defaultStyle: o, values: s, render: c } = e;
	return (0, x.useMemo)(() => {
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
function Wf(e, t) {
	let n = (0, x.useContext)(e);
	if (t === null) return null;
	if (n && typeof n == "object" && "slots" in n && n.slots) {
		let e = t || Vf;
		if (!n.slots[e]) {
			let e = new Intl.ListFormat().format(Object.keys(n.slots).map((e) => `"${e}"`)), r = t ? `Invalid slot "${t}".` : "A slot prop is required.";
			throw Error(`${r} Valid slot names are ${e}.`);
		}
		return n.slots[e];
	}
	return n;
}
function Gf(e, t, n) {
	let { ref: r, ...i } = Wf(n, e.slot) || {}, a = Nr((0, x.useMemo)(() => mr(t, r), [t, r])), o = H(i, e);
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
function Kf(e = !0) {
	let [t, n] = (0, x.useState)(e), r = (0, x.useRef)(!1), i = (0, x.useCallback)((e) => {
		r.current = !0, n(!!e);
	}, []);
	return V(() => {
		r.current || n(!1);
	}, []), [i, t];
}
function qf(e) {
	let t = /^(data-.*)$/, n = {};
	for (let r in e) t.test(r) || (n[r] = e[r]);
	return n;
}
function Jf(e, t, n) {
	let { render: r, ...i } = t, a = (0, x.useRef)(null), o = (0, x.useMemo)(() => mr(n, a), [n, a]);
	V(() => {}, [e, r]);
	let s = {
		...i,
		ref: o
	};
	return r ? r(s, void 0) : /*#__PURE__*/ x.createElement(e, s);
}
var Yf = {}, Xf = new Proxy({}, { get(e, t) {
	if (typeof t != "string") return;
	let n = Yf[t];
	return n || (n = /*#__PURE__*/ (0, x.forwardRef)(Jf.bind(null, t)), Yf[t] = n), n;
} }), Zf = /*#__PURE__*/ (0, x.createContext)(null), Qf = /*#__PURE__*/ (0, x.createContext)(null), $f = /*#__PURE__*/ (0, x.createContext)(null), ep = {
	CollectionRoot({ collection: e, renderDropIndicator: t }) {
		return tp(e, null, t);
	},
	CollectionBranch({ collection: e, parent: t, renderDropIndicator: n }) {
		return tp(e, t, n);
	}
};
function tp(e, t, n) {
	return yt({
		items: t ? e.getChildren(t.key) : e,
		dependencies: [n],
		children(t) {
			if (t.type === "content") return /*#__PURE__*/ x.createElement(x.Fragment, null);
			let r = t.render(t);
			return !n || t.type !== "item" ? r : /*#__PURE__*/ x.createElement(x.Fragment, null, n({
				type: "item",
				key: t.key,
				dropPosition: "before"
			}), r, np(e, t, n));
		}
	});
}
function np(e, t, n) {
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
			/*#__PURE__*/ (0, x.isValidElement)(t) && s.push(/*#__PURE__*/ (0, x.cloneElement)(t, { key: `${r.key}-after` })), r = r.parentKey == null ? null : e.getItem(r.parentKey);
		}
	}
	return s;
}
var rp = /*#__PURE__*/ (0, x.createContext)(ep), ip = /*#__PURE__*/ (0, x.createContext)({}), ap = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, ip);
	let { elementType: n = "label", ...r } = e, i = Xf[n];
	return /*#__PURE__*/ x.createElement(i, {
		className: "react-aria-Label",
		...r,
		ref: t
	});
}), op = /*#__PURE__*/ (0, x.createContext)(null), sp = /*#__PURE__*/ (0, x.createContext)({}), cp = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, sp);
	let n = e, { isPending: r } = n, { buttonProps: i, isPressed: a } = xa(e, t);
	i = up(i, r);
	let { focusProps: o, isFocused: s, isFocusVisible: c } = hc(e), { hoverProps: l, isHovered: u } = Sc({
		...e,
		isDisabled: e.isDisabled || r
	}), d = {
		isHovered: u,
		isPressed: (n.isPressed || a) && !r,
		isFocused: s,
		isFocusVisible: c,
		isDisabled: e.isDisabled || !1,
		isPending: r ?? !1
	}, f = Uf({
		...e,
		values: d,
		defaultClassName: "react-aria-Button"
	}), p = dr(i.id), m = dr(), h = i["aria-labelledby"];
	r && (h ? h = `${h} ${m}` : i["aria-label"] && (h = `${p} ${m}`));
	let g = (0, x.useRef)(r);
	(0, x.useEffect)(() => {
		let e = { "aria-labelledby": h || p };
		(!g.current && s && r || g.current && s && !r) && Qa(e, "assertive"), g.current = r;
	}, [
		r,
		s,
		h,
		p
	]);
	let _ = U(e, { global: !0 });
	return delete _.onClick, /*#__PURE__*/ x.createElement(Xf.button, {
		...H(_, f, i, o, l),
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
	}, /*#__PURE__*/ x.createElement(op.Provider, { value: { id: m } }, f.children));
}), lp = /Focus|Blur|Hover|Pointer(Enter|Leave|Over|Out)|Mouse(Enter|Leave|Over|Out)/;
function up(e, t) {
	if (t) {
		for (let t in e) t.startsWith("on") && !lp.test(t) && (e[t] = void 0);
		e.href = void 0, e.target = void 0;
	}
	return e;
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Heading.mjs
var dp = /*#__PURE__*/ (0, x.createContext)({}), fp = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	[e, t] = Gf(e, t, dp);
	let { children: n, level: r = 3, className: i, ...a } = e, o = Xf[`h${r}`];
	return /*#__PURE__*/ x.createElement(o, {
		...a,
		ref: t,
		className: i ?? "react-aria-Heading"
	}, n);
}), pp = /*#__PURE__*/ (0, x.createContext)({}), mp = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, pp);
	let { elementType: n = "span", ...r } = e, i = Xf[n];
	return /*#__PURE__*/ x.createElement(i, {
		className: "react-aria-Text",
		...r,
		ref: t
	});
}), hp = /*#__PURE__*/ (0, x.createContext)(null), gp = /*#__PURE__*/ (0, x.createContext)(null), _p = /*#__PURE__*/ (0, x.createContext)(null), vp = /*#__PURE__*/ (0, x.createContext)(null), yp = /*#__PURE__*/ (0, x.createContext)(null);
function bp(e, t) {
	let { validationBehavior: n } = Wf(gp) || {}, r = e.validationBehavior ?? n ?? "native", i = (0, x.useContext)(vp), a = Nr((0, x.useMemo)(() => mr(t, e.inputRef === void 0 ? null : e.inputRef), [t, e.inputRef])), o = {
		...qf(e),
		children: typeof e.children == "function" || e.children,
		value: e.value,
		validationBehavior: r
	};
	return [i ? K(o, i, a) : ko(o, Io(e), a), a];
}
var xp = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { inputRef: n = null, ...r } = e;
	[e, t] = Gf(r, t, _p);
	let [i, a] = bp(e, n);
	return /*#__PURE__*/ x.createElement(yp.Provider, { value: {
		...i,
		inputRef: a,
		defaultClassName: "react-aria-Checkbox",
		isIndeterminate: e.isIndeterminate,
		isRequired: e.isRequired
	} }, /*#__PURE__*/ x.createElement(Sp, {
		...e,
		ref: t
	}));
}), Sp = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { labelProps: n, inputProps: r, isSelected: i, isDisabled: a, isReadOnly: o, isPressed: s, isInvalid: c, inputRef: l, defaultClassName: u, isIndeterminate: d, isRequired: f } = (0, x.useContext)(yp), { isFocused: p, isFocusVisible: m, focusProps: h } = hc(), g = a || o, { hoverProps: _, isHovered: v } = Sc({
		...e,
		isDisabled: g
	}), y = Uf({
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
	}), b = U(e, { global: !0 });
	return delete b.id, delete b.onClick, /*#__PURE__*/ x.createElement(Xf.label, {
		...H(b, n, _, y),
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
	}, /*#__PURE__*/ x.createElement(Bo, { elementType: "span" }, /*#__PURE__*/ x.createElement("input", {
		...H(r, h),
		ref: l
	})), y.children);
}), Cp = /*#__PURE__*/ (0, x.createContext)({}), wp = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	[e, t] = Gf(e, t, Cp);
	let { isDisabled: n, isInvalid: r, isReadOnly: i, onHoverStart: a, onHoverChange: o, onHoverEnd: s, ...c } = e;
	n ??= !!e["aria-disabled"] && e["aria-disabled"] !== "false", r ??= !!e["aria-invalid"] && e["aria-invalid"] !== "false";
	let { hoverProps: l, isHovered: u } = Sc({
		onHoverStart: a,
		onHoverChange: o,
		onHoverEnd: s,
		isDisabled: n
	}), { isFocused: d, isFocusVisible: f, focusProps: p } = hc({ within: !0 }), m = Uf({
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
	return /*#__PURE__*/ x.createElement(Xf.div, {
		...H(c, p, l),
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
}), Tp = /*#__PURE__*/ (0, x.createContext)({}), Ep = (e) => {
	let { onHoverStart: t, onHoverChange: n, onHoverEnd: r, ...i } = e;
	return i;
}, Dp = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, Tp);
	let { hoverProps: n, isHovered: r } = Sc({
		...e,
		isDisabled: e.disabled
	}), { isFocused: i, isFocusVisible: a, focusProps: o } = hc({
		isTextInput: !0,
		autoFocus: e.autoFocus
	}), s = !!e["aria-invalid"] && e["aria-invalid"] !== "false", c = Uf({
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
	return /*#__PURE__*/ x.createElement(Xf.input, {
		...H(Ep(e), o, n),
		...c,
		ref: t,
		"data-focused": i || void 0,
		"data-disabled": e.disabled || void 0,
		"data-hovered": r || void 0,
		"data-focus-visible": a || void 0,
		"data-invalid": s || void 0
	});
}), Op = {};
Op = {
	colorSwatchPicker: "تغييرات الألوان",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "حدد عنصرًا",
	tableResizer: "أداة تغيير الحجم"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/bg-BG.mjs
var kp = {};
kp = {
	colorSwatchPicker: "Цветови мостри",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Изберете предмет",
	tableResizer: "Преоразмерител"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/cs-CZ.mjs
var Ap = {};
Ap = {
	colorSwatchPicker: "Vzorky barev",
	dropzoneLabel: "Místo pro přetažení",
	selectPlaceholder: "Vyberte položku",
	tableResizer: "Změna velikosti"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/da-DK.mjs
var jp = {};
jp = {
	colorSwatchPicker: "Farveprøver",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Vælg et element",
	tableResizer: "Størrelsesændring"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/de-DE.mjs
var Mp = {};
Mp = {
	colorSwatchPicker: "Farbfelder",
	dropzoneLabel: "Ablegebereich",
	selectPlaceholder: "Element wählen",
	tableResizer: "Größenanpassung"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/el-GR.mjs
var Np = {};
Np = {
	colorSwatchPicker: "Χρωματικά δείγματα",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Επιλέξτε ένα αντικείμενο",
	tableResizer: "Αλλαγή μεγέθους"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/en-US.mjs
var Pp = {};
Pp = {
	selectPlaceholder: "Select an item",
	tableResizer: "Resizer",
	dropzoneLabel: "DropZone",
	colorSwatchPicker: "Color swatches"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/es-ES.mjs
var Fp = {};
Fp = {
	colorSwatchPicker: "Muestras de colores",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Seleccionar un artículo",
	tableResizer: "Cambiador de tamaño"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/et-EE.mjs
var Ip = {};
Ip = {
	colorSwatchPicker: "Värvinäidised",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Valige üksus",
	tableResizer: "Suuruse muutja"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/fi-FI.mjs
var Lp = {};
Lp = {
	colorSwatchPicker: "Värimallit",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Valitse kohde",
	tableResizer: "Koon muuttaja"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/fr-FR.mjs
var Rp = {};
Rp = {
	colorSwatchPicker: "Échantillons de couleurs",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Sélectionner un élément",
	tableResizer: "Redimensionneur"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/he-IL.mjs
var zp = {};
zp = {
	colorSwatchPicker: "דוגמיות צבע",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "בחר פריט",
	tableResizer: "שינוי גודל"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/hr-HR.mjs
var Bp = {};
Bp = {
	colorSwatchPicker: "Uzorci boja",
	dropzoneLabel: "Zona spuštanja",
	selectPlaceholder: "Odaberite stavku",
	tableResizer: "Promjena veličine"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/hu-HU.mjs
var Vp = {};
Vp = {
	colorSwatchPicker: "Színtárak",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Válasszon ki egy elemet",
	tableResizer: "Átméretező"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/it-IT.mjs
var Hp = {};
Hp = {
	colorSwatchPicker: "Campioni di colore",
	dropzoneLabel: "Zona di rilascio",
	selectPlaceholder: "Seleziona un elemento",
	tableResizer: "Ridimensionamento"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ja-JP.mjs
var Up = {};
Up = {
	colorSwatchPicker: "カラースウォッチ",
	dropzoneLabel: "ドロップゾーン",
	selectPlaceholder: "項目を選択",
	tableResizer: "サイズ変更ツール"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ko-KR.mjs
var Wp = {};
Wp = {
	colorSwatchPicker: "색상 견본",
	dropzoneLabel: "드롭 영역",
	selectPlaceholder: "항목 선택",
	tableResizer: "크기 조정기"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/lt-LT.mjs
var Gp = {};
Gp = {
	colorSwatchPicker: "Spalvų pavyzdžiai",
	dropzoneLabel: "„DropZone“",
	selectPlaceholder: "Pasirinkite elementą",
	tableResizer: "Dydžio keitiklis"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/lv-LV.mjs
var Kp = {};
Kp = {
	colorSwatchPicker: "Krāsu paraugi",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Izvēlēties vienumu",
	tableResizer: "Izmēra mainītājs"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/nb-NO.mjs
var qp = {};
qp = {
	colorSwatchPicker: "Fargekart",
	dropzoneLabel: "Droppsone",
	selectPlaceholder: "Velg et element",
	tableResizer: "Størrelsesendrer"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/nl-NL.mjs
var Jp = {};
Jp = {
	colorSwatchPicker: "kleurstalen",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Selecteer een item",
	tableResizer: "Resizer"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/pl-PL.mjs
var Yp = {};
Yp = {
	colorSwatchPicker: "Próbki kolorów",
	dropzoneLabel: "Strefa upuszczania",
	selectPlaceholder: "Wybierz element",
	tableResizer: "Zmiana rozmiaru"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/pt-BR.mjs
var Xp = {};
Xp = {
	colorSwatchPicker: "Amostras de cores",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Selecione um item",
	tableResizer: "Redimensionador"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/pt-PT.mjs
var Zp = {};
Zp = {
	colorSwatchPicker: "Amostras de cores",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Selecione um item",
	tableResizer: "Redimensionador"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ro-RO.mjs
var Qp = {};
Qp = {
	colorSwatchPicker: "Specimene de culoare",
	dropzoneLabel: "Zonă de plasare",
	selectPlaceholder: "Selectați un element",
	tableResizer: "Instrument de redimensionare"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/ru-RU.mjs
var $p = {};
$p = {
	colorSwatchPicker: "Цветовые образцы",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Выберите элемент",
	tableResizer: "Средство изменения размера"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sk-SK.mjs
var em = {};
em = {
	colorSwatchPicker: "Vzorkovníky farieb",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Vyberte položku",
	tableResizer: "Nástroj na zmenu veľkosti"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sl-SI.mjs
var tm = {};
tm = {
	colorSwatchPicker: "Barvne palete",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Izberite element",
	tableResizer: "Spreminjanje velikosti"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sr-SP.mjs
var nm = {};
nm = {
	colorSwatchPicker: "Uzorci boje",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Izaberite stavku",
	tableResizer: "Promena veličine"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/sv-SE.mjs
var rm = {};
rm = {
	colorSwatchPicker: "Färgrutor",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Välj en artikel",
	tableResizer: "Storleksändrare"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/tr-TR.mjs
var im = {};
im = {
	colorSwatchPicker: "Renk örnekleri",
	dropzoneLabel: "Bırakma Bölgesi",
	selectPlaceholder: "Bir öğe seçin",
	tableResizer: "Yeniden boyutlandırıcı"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/uk-UA.mjs
var am = {};
am = {
	colorSwatchPicker: "Зразки кольорів",
	dropzoneLabel: "DropZone",
	selectPlaceholder: "Виберіть елемент",
	tableResizer: "Засіб змінення розміру"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/zh-CN.mjs
var om = {};
om = {
	colorSwatchPicker: "颜色色板",
	dropzoneLabel: "放置区域",
	selectPlaceholder: "选择一个项目",
	tableResizer: "尺寸调整器"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intl/zh-TW.mjs
var sm = {};
sm = {
	colorSwatchPicker: "色票",
	dropzoneLabel: "放置區",
	selectPlaceholder: "選取項目",
	tableResizer: "大小調整器"
};
//#endregion
//#region node_modules/react-aria-components/dist/private/intlStrings.mjs
var cm = {};
cm = {
	"ar-AE": Op,
	"bg-BG": kp,
	"cs-CZ": Ap,
	"da-DK": jp,
	"de-DE": Mp,
	"el-GR": Np,
	"en-US": Pp,
	"es-ES": Fp,
	"et-EE": Ip,
	"fi-FI": Lp,
	"fr-FR": Rp,
	"he-IL": zp,
	"hr-HR": Bp,
	"hu-HU": Vp,
	"it-IT": Hp,
	"ja-JP": Up,
	"ko-KR": Wp,
	"lt-LT": Gp,
	"lv-LV": Kp,
	"nb-NO": qp,
	"nl-NL": Jp,
	"pl-PL": Yp,
	"pt-BR": Xp,
	"pt-PT": Zp,
	"ro-RO": Qp,
	"ru-RU": $p,
	"sk-SK": em,
	"sl-SI": tm,
	"sr-SP": nm,
	"sv-SE": rm,
	"tr-TR": im,
	"uk-UA": am,
	"zh-CN": om,
	"zh-TW": sm
};
//#endregion
//#region node_modules/react-aria-components/dist/private/DragAndDrop.mjs
var lm = /*#__PURE__*/ (0, x.createContext)({}), um = /*#__PURE__*/ (0, x.createContext)(null), dm = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { render: n } = (0, x.useContext)(um);
	return /*#__PURE__*/ x.createElement(x.Fragment, null, n(e, t));
});
function fm(e, t) {
	let n = e?.renderDropIndicator, r = e?.isVirtualDragging?.(), i = (0, x.useCallback)((e) => {
		if (r || t?.isDropTarget(e)) return n ? n(e) : /*#__PURE__*/ x.createElement(dm, { target: e });
	}, [
		t?.target,
		r,
		n
	]);
	return e?.useDropIndicator ? i : void 0;
}
function pm(e, t, n) {
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
	return (0, x.useMemo)(() => new Set([r, i].filter((e) => e != null)), [r, i]);
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Header.mjs
var mm = /*#__PURE__*/ (0, x.createContext)({}), hm = /*#__PURE__*/ (0, x.createContext)(null);
function gm(e) {
	let t = (0, x.useRef)({});
	return /*#__PURE__*/ x.createElement(hm.Provider, { value: t }, e.children);
}
//#endregion
//#region node_modules/react-aria-components/dist/private/SelectionIndicator.mjs
var _m = /*#__PURE__*/ (0, x.createContext)({ isSelected: !1 }), vm = /*#__PURE__*/ (0, x.createContext)({});
(class extends ut {
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
function ym(e) {
	let t = x.version.split(".");
	return parseInt(t[0], 10) >= 19 ? e : e ? "true" : void 0;
}
//#endregion
//#region node_modules/react-stately/dist/private/list/ListCollection.mjs
var bm = class {
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
}, xm = class e extends Set {
	constructor(t, n, r) {
		super(t), t instanceof e ? (this.anchorKey = n ?? t.anchorKey, this.currentKey = r ?? t.currentKey) : (this.anchorKey = n ?? null, this.currentKey = r ?? null);
	}
};
//#endregion
//#region node_modules/react-stately/dist/private/selection/useMultipleSelectionState.mjs
function Sm(e, t) {
	if (e.size !== t.size) return !1;
	for (let n of e) if (!t.has(n)) return !1;
	return !0;
}
function Cm(e) {
	let { selectionMode: t = "none", disallowEmptySelection: n = !1, allowDuplicateSelectionEvents: r, selectionBehavior: i = "toggle", disabledBehavior: a = "all" } = e, o = (0, x.useRef)(!1), [, s] = (0, x.useState)(!1), c = (0, x.useRef)(null), l = (0, x.useRef)(null), [, u] = (0, x.useState)(null), [d, f] = Fo((0, x.useMemo)(() => wm(e.selectedKeys), [e.selectedKeys]), (0, x.useMemo)(() => wm(e.defaultSelectedKeys, new xm()), [e.defaultSelectedKeys]), e.onSelectionChange), p = (0, x.useMemo)(() => e.disabledKeys ? new Set(e.disabledKeys) : /* @__PURE__ */ new Set(), [e.disabledKeys]), [m, h] = (0, x.useState)(i);
	i === "replace" && m === "toggle" && typeof d == "object" && d.size === 0 && h("replace");
	let g = (0, x.useRef)(i);
	return (0, x.useEffect)(() => {
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
			(r || !Sm(e, d)) && f(e);
		},
		disabledKeys: p,
		disabledBehavior: a
	};
}
function wm(e, t) {
	return e ? e === "all" ? "all" : new xm(e) : t;
}
//#endregion
//#region node_modules/react-stately/dist/private/selection/SelectionManager.mjs
var Tm = class e {
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
			(!e || n && tc(this.collection, n, e) < 0) && (e = n);
		}
		return e?.key ?? null;
	}
	get lastSelectedKey() {
		let e = null;
		for (let t of this.state.selectedKeys) {
			let n = this.collection.getItem(t);
			(!e || n && tc(this.collection, n, e) > 0) && (e = n);
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
		if (this.state.selectedKeys === "all") n = new xm([t], t, t);
		else {
			let e = this.state.selectedKeys, r = e.anchorKey ?? t;
			n = new xm(e, r, t);
			for (let i of this.getKeyRange(r, e.currentKey ?? t)) n.delete(i);
			for (let e of this.getKeyRange(t, r)) this.canSelectItem(e) && n.add(e);
		}
		this.state.setSelectedKeys(n);
	}
	getKeyRange(e, t) {
		let n = this.collection.getItem(e), r = this.collection.getItem(t);
		return n && r ? tc(this.collection, n, r) <= 0 ? this.getKeyRangeInternal(e, t) : this.getKeyRangeInternal(t, e) : [];
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
		let n = new xm(this.state.selectedKeys === "all" ? this.getSelectAllKeys() : this.state.selectedKeys);
		n.has(t) ? n.delete(t) : this.canSelectItem(t) && (n.add(t), n.anchorKey = t, n.currentKey = t), !(this.disallowEmptySelection && n.size === 0) && this.state.setSelectedKeys(n);
	}
	replaceSelection(e) {
		if (this.selectionMode === "none") return;
		let t = this.getKey(e);
		if (t == null) return;
		let n = this.canSelectItem(t) ? new xm([t], t, t) : new xm();
		this.state.setSelectedKeys(n);
	}
	setSelectedKeys(e) {
		if (this.selectionMode === "none") return;
		let t = new xm();
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
					i?.type === "item" && t.push(r), i?.hasChildNodes && (this.allowsCellSelection || i.type !== "item") && n($s(Qs(i, e))?.key ?? null);
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
		!this.disallowEmptySelection && (this.state.selectedKeys === "all" || this.state.selectedKeys.size > 0) && this.state.setSelectedKeys(new xm());
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
}, Em = class {
	build(e, t) {
		return this.context = t, Dm(() => this.iterateCollection(e));
	}
	*iterateCollection(e) {
		let { children: t, items: n } = e;
		if (x.isValidElement(t) && t.type === x.Fragment) yield* this.iterateCollection({
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
			x.Children.forEach(t, (t) => {
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
		if (x.isValidElement(e.element) && e.element.type === x.Fragment) {
			let i = [];
			x.Children.forEach(e.element.props.children, (e) => {
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
		if (x.isValidElement(i)) {
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
					wrapper: Om(e.wrapper, a.wrapper)
				}, this.getChildState(t, a), n ? `${n}${i.key}` : i.key, r)];
				for (let t of u) {
					if (t.value = a.value ?? e.value ?? null, t.value && this.cache.set(t.value, t), e.type && t.type !== e.type) throw Error(`Unsupported type <${km(t.type)}> in <${km(r?.type ?? "unknown parent type")}>. Only <${km(e.type)}> is supported.`);
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
			childNodes: Dm(function* () {
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
function Dm(e) {
	let t = [], n = null;
	return { *[Symbol.iterator]() {
		for (let e of t) yield e;
		n ||= e();
		for (let e of n) t.push(e), yield e;
	} };
}
function Om(e, t) {
	if (e && t) return (n) => e(t(n));
	if (e) return e;
	if (t) return t;
}
function km(e) {
	return e[0].toUpperCase() + e.slice(1);
}
//#endregion
//#region node_modules/react-stately/dist/private/collections/useCollection.mjs
function Am(e, t, n) {
	let r = (0, x.useMemo)(() => new Em(), []), { children: i, items: a, collection: o } = e;
	return (0, x.useMemo)(() => o || t(r.build({
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
function jm(e) {
	let { filter: t, layoutDelegate: n } = e, r = Cm(e), i = (0, x.useMemo)(() => e.disabledKeys ? new Set(e.disabledKeys) : /* @__PURE__ */ new Set(), [e.disabledKeys]), a = Am(e, (0, x.useCallback)((e) => t ? new bm(t(e)) : new bm(e), [t]), (0, x.useMemo)(() => ({ suppressTextValueWarning: e.suppressTextValueWarning }), [e.suppressTextValueWarning])), o = (0, x.useMemo)(() => new Tm(a, r, { layoutDelegate: n }), [
		a,
		r,
		n
	]);
	return Nm(a, o), {
		collection: a,
		disabledKeys: i,
		selectionManager: o
	};
}
function Mm(e, t) {
	let n = (0, x.useMemo)(() => t ? e.collection.filter(t) : e.collection, [e.collection, t]), r = e.selectionManager.withCollection(n);
	return Nm(n, r), {
		collection: n,
		selectionManager: r,
		disabledKeys: e.disabledKeys
	};
}
function Nm(e, t) {
	let n = (0, x.useRef)(null);
	(0, x.useEffect)(() => {
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
function Pm(e, t) {
	let { collection: n, onLoadMore: r, scrollOffset: i = 1, direction: a = "end" } = e, o = (0, x.useRef)(null), s = yi((e) => {
		for (let t of e) t.isIntersecting && r && r();
	});
	V(() => {
		if (t.current) {
			let e = 100 * i, n = a === "start" ? `${e}% 0px 0px 0px` : `0px ${e}% ${e}% ${e}%`;
			o.current = new IntersectionObserver(s, {
				root: to(t?.current),
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
var Fm = /*#__PURE__*/ (0, x.createContext)(null), Im = /*#__PURE__*/ (0, x.createContext)(null), Lm = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	[e, t] = Gf(e, t, Fm);
	let n = (0, x.useContext)(Im);
	return n ? /*#__PURE__*/ x.createElement(zm, {
		state: n,
		props: e,
		listBoxRef: t
	}) : /*#__PURE__*/ x.createElement(Xr, { content: /*#__PURE__*/ x.createElement(si, e) }, (n) => /*#__PURE__*/ x.createElement(Rm, {
		props: e,
		listBoxRef: t,
		collection: n
	}));
});
function Rm({ props: e, listBoxRef: t, collection: n }) {
	e = {
		...e,
		collection: n,
		children: null,
		items: null
	};
	let { layoutDelegate: r } = (0, x.useContext)(rp), i = jm({
		...e,
		layoutDelegate: r
	});
	return /*#__PURE__*/ x.createElement(zm, {
		state: i,
		props: e,
		listBoxRef: t
	});
}
function zm({ state: e, props: t, listBoxRef: n }) {
	[t, n] = Gf(t, n, Zf);
	let { dragAndDropHooks: r, layout: i = "stack", orientation: a = "vertical", filter: o } = t, s = Mm(e, o), { collection: c, selectionManager: l } = s, u = !!r?.useDraggableCollectionState, d = !!r?.useDroppableCollectionState, { direction: f } = Mi(), { disabledBehavior: p, disabledKeys: m } = l, h = oc({
		usage: "search",
		sensitivity: "base"
	}), { isVirtualized: g, layoutDelegate: _, dropTargetDelegate: v, CollectionRoot: y } = (0, x.useContext)(rp), b = (0, x.useMemo)(() => t.keyboardDelegate || new rs({
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
	]), { listBoxProps: S } = kc({
		...t,
		shouldSelectOnPressUp: u || t.shouldSelectOnPressUp,
		keyboardDelegate: b,
		isVirtualized: g
	}, s, n);
	(0, x.useRef)(u), (0, x.useRef)(d), (0, x.useEffect)(() => {}, [u, d]);
	let C, w, T, E = !1, D = null, O = (0, x.useRef)(null);
	if (u && r) {
		C = r.useDraggableCollectionState({
			collection: c,
			selectionManager: l,
			preview: r.renderDragPreview ? O : void 0
		}), r.useDraggableCollection({}, C, n);
		let e = r.DragPreview;
		D = r.renderDragPreview ? /*#__PURE__*/ x.createElement(e, { ref: O }, r.renderDragPreview) : null;
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
			keyboardDelegate: b,
			dropTargetDelegate: e
		}, w, n), E = w.isDropTarget({ type: "root" });
	}
	let { focusProps: k, isFocused: A, isFocusVisible: ee } = hc(), j = s.collection.size === 0, te = {
		isDropTarget: E,
		isEmpty: j,
		isFocused: A,
		isFocusVisible: ee,
		layout: t.layout || "stack",
		orientation: a,
		state: s
	}, M = Uf({
		...t,
		children: void 0,
		defaultClassName: "react-aria-ListBox",
		values: te
	}), ne = null;
	j && t.renderEmptyState && (ne = /*#__PURE__*/ x.createElement("div", {
		role: "option",
		style: { display: "contents" }
	}, t.renderEmptyState(te)));
	let N = U(t, { global: !0 });
	return /*#__PURE__*/ x.createElement(Ea, null, /*#__PURE__*/ x.createElement(Xf.div, {
		...H(N, M, S, k, T?.collectionProps),
		ref: n,
		slot: t.slot || void 0,
		onScroll: t.onScroll,
		"data-drop-target": E || void 0,
		"data-empty": j || void 0,
		"data-focused": A || void 0,
		"data-focus-visible": ee || void 0,
		"data-layout": t.layout || "stack",
		"data-orientation": a
	}, /*#__PURE__*/ x.createElement(Hf, { values: [
		[Fm, t],
		[Im, s],
		[lm, {
			dragAndDropHooks: r,
			dragState: C,
			dropState: w
		}],
		[vm, { elementType: "div" }],
		[um, { render: Hm }],
		[$f, {
			name: "ListBoxSection",
			render: Bm
		}]
	] }, /*#__PURE__*/ x.createElement(gm, null, /*#__PURE__*/ x.createElement(y, {
		collection: c,
		scrollRef: n,
		persistedKeys: pm(l, r, w),
		renderDropIndicator: fm(r, w)
	}))), ne, D));
}
function Bm(e, t, n, r = "react-aria-ListBoxSection") {
	let i = (0, x.useContext)(Im), { dragAndDropHooks: a, dropState: o } = (0, x.useContext)(lm), { CollectionBranch: s } = (0, x.useContext)(rp), [c, l] = Kf(), { headingProps: u, groupProps: d } = Ac({
		heading: l,
		"aria-label": e["aria-label"] ?? void 0
	}), f = Uf({
		...e,
		id: void 0,
		children: void 0,
		defaultClassName: r,
		values: void 0
	}), p = U(e, { global: !0 });
	return delete p.id, /*#__PURE__*/ x.createElement(Xf.section, {
		...H(p, f, d),
		ref: t
	}, /*#__PURE__*/ x.createElement(mm.Provider, { value: {
		...u,
		ref: c
	} }, /*#__PURE__*/ x.createElement(s, {
		collection: i.collection,
		parent: n,
		renderDropIndicator: fm(a, o)
	})));
}
var Vm = /*#__PURE__*/ ii(pt, function(e, t, n) {
	let r = Nr(t), i = (0, x.useContext)(Im), { dragAndDropHooks: a, dragState: o, dropState: s } = (0, x.useContext)(lm), c = o && !(o.isDisabled || o.selectionManager.isDisabled(n.key)), { optionProps: l, labelProps: u, descriptionProps: d, ...f } = jc({
		key: n.key,
		"aria-label": e?.["aria-label"]
	}, i, r), { hoverProps: p, isHovered: m } = Sc({
		isDisabled: !f.allowsSelection && !f.hasAction && !c,
		onHoverStart: n.props.onHoverStart,
		onHoverChange: n.props.onHoverChange,
		onHoverEnd: n.props.onHoverEnd
	}), { keyboardProps: h } = Mr(e), { focusProps: g } = vr(e), _ = null;
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
	let y = o && o.isDragging(n.key), b = Uf({
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
	(0, x.useEffect)(() => {
		n.textValue;
	}, [n.textValue]);
	let S = e.href ? Xf.a : Xf.div, C = U(e, { global: !0 });
	return delete C.id, delete C.onClick, e.href && l.tabIndex == null && (l.tabIndex = -1), /*#__PURE__*/ x.createElement(S, {
		...H(C, b, l, p, h, g, _?.dragProps, v?.dropProps),
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
	}, /*#__PURE__*/ x.createElement(Hf, { values: [[pp, { slots: {
		[Vf]: u,
		label: u,
		description: d
	} }], [_m, { isSelected: f.isSelected }]] }, b.children));
});
function Hm(e, t) {
	t = Nr(t);
	let { dragAndDropHooks: n, dropState: r } = (0, x.useContext)(lm), { dropIndicatorProps: i, isHidden: a, isDropTarget: o } = n.useDropIndicator(e, r, t);
	return a ? null : /*#__PURE__*/ x.createElement(Wm, {
		...e,
		dropIndicatorProps: i,
		isDropTarget: o,
		ref: t
	});
}
function Um(e, t) {
	let { dropIndicatorProps: n, isDropTarget: r, ...i } = e, a = Uf({
		...i,
		defaultClassName: "react-aria-DropIndicator",
		values: { isDropTarget: r }
	});
	return /*#__PURE__*/ x.createElement(x.Fragment, null, /*#__PURE__*/ x.createElement(Xf.div, {
		...n,
		...a,
		role: "option",
		ref: t,
		"data-drop-target": r || void 0
	}));
}
var Wm = /*#__PURE__*/ (0, x.forwardRef)(Um);
ii(ft, function(e, t, n) {
	let r = (0, x.useContext)(Im), { isLoading: i, onLoadMore: a, scrollOffset: o, ...s } = e, c = (0, x.useRef)(null);
	Pm((0, x.useMemo)(() => ({
		onLoadMore: a,
		collection: r?.collection,
		sentinelRef: c,
		scrollOffset: o
	}), [
		a,
		o,
		r?.collection
	]), c);
	let l = Uf({
		...s,
		id: void 0,
		children: n.rendered,
		defaultClassName: "react-aria-ListBoxLoadingIndicator",
		values: void 0
	});
	return /*#__PURE__*/ x.createElement(x.Fragment, null, /*#__PURE__*/ x.createElement("div", {
		style: {
			position: "relative",
			width: 0,
			height: 0
		},
		inert: ym(!0)
	}, /*#__PURE__*/ x.createElement("div", {
		"data-testid": "loadMoreSentinel",
		ref: c,
		style: {
			position: "absolute",
			height: 1,
			width: 1
		}
	})), i && l.children && /*#__PURE__*/ x.createElement(x.Fragment, null, /*#__PURE__*/ x.createElement(Xf.div, {
		...H(U(e, { global: !0 }), { tabIndex: -1 }),
		...l,
		role: "option",
		ref: t
	}, l.children)));
});
//#endregion
//#region node_modules/react-aria-components/dist/private/OverlayArrow.mjs
var Gm = /*#__PURE__*/ (0, x.createContext)({ placement: "bottom" });
//#endregion
//#region node_modules/react-stately/dist/private/overlays/useOverlayTriggerState.mjs
function Km(e) {
	let [t, n] = Fo(e.isOpen, e.defaultOpen || !1, e.onOpenChange), [r, i] = (0, x.useState)(null);
	return {
		isOpen: t,
		setOpen: n,
		open: (0, x.useCallback)(() => {
			n(!0);
		}, [n]),
		close: (0, x.useCallback)(() => {
			n(!1);
		}, [n]),
		toggle: (0, x.useCallback)(() => {
			n(!t);
		}, [n, t]),
		point: r,
		setPoint: i
	};
}
//#endregion
//#region node_modules/react-aria/dist/private/utils/animation.mjs
function qm(e, t = !0) {
	let [n, r] = (0, x.useState)(!0), i = n && t;
	return V(() => {
		if (i && e.current && "getAnimations" in e.current) for (let t of e.current.getAnimations()) t instanceof CSSTransition && t.cancel();
	}, [e, i]), Ym(e, i, (0, x.useCallback)(() => r(!1), [])), i;
}
function Jm(e, t) {
	let [n, r] = (0, x.useState)(t ? "open" : "closed");
	switch (n) {
		case "open":
			t || r("exiting");
			break;
		case "closed":
		case "exiting": t && r("open");
	}
	let i = n === "exiting";
	return Ym(e, i, (0, x.useCallback)(() => {
		r((e) => e === "exiting" ? "closed" : e);
	}, [])), i;
}
function Ym(e, t, n) {
	V(() => {
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
				r || (0, Kr.flushSync)(() => {
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
var Xm = /*#__PURE__*/ (0, x.createContext)(null), Zm = /*#__PURE__*/ (0, x.createContext)(null), Qm = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	[e, t] = Gf(e, t, Xm);
	let n = (0, x.useContext)(th), r = Km(e), i = e.isOpen != null || e.defaultOpen != null || !n ? r : n, a = Jm(t, i.isOpen), o = e.isExiting || !e.shouldSkipAnimation && a || !1, s = Vr(), { direction: c } = Mi();
	if (s) {
		let t = e.children;
		return typeof t == "function" && (t = t({
			trigger: e.trigger || null,
			placement: "bottom",
			isEntering: !1,
			isExiting: !1,
			defaultChildren: null
		})), /*#__PURE__*/ x.createElement(x.Fragment, null, t);
	}
	return i && !i.isOpen && !o ? null : /*#__PURE__*/ x.createElement($m, {
		...e,
		triggerRef: e.triggerRef,
		state: i,
		popoverRef: t,
		isExiting: o,
		dir: c
	});
});
function $m({ state: e, isExiting: t, UNSTABLE_portalContainer: n, clearContexts: r, ...i }) {
	let a = (0, x.useRef)(null), o = (0, x.useRef)(null), s = (0, x.useContext)(Zm), c = s && i.trigger === "SubmenuTrigger", { popoverProps: l, underlayProps: u, arrowProps: d, placement: f, triggerAnchorPoint: p } = eu({
		...i,
		offset: i.offset ?? 8,
		arrowRef: a,
		groupRef: c ? s : o
	}, e), m = i.popoverRef, h = qm(m, !!f), g = i.isEntering || !i.shouldSkipAnimation && h || !1, _ = Uf({
		...i,
		defaultClassName: "react-aria-Popover",
		values: {
			trigger: i.trigger || null,
			placement: f,
			isEntering: g,
			isExiting: t
		}
	}), v = !i.isNonModal || i.trigger === "SubmenuTrigger" || i.trigger === "PreviewTrigger", [y, b] = (0, x.useState)(i.trigger === "PreviewTrigger");
	V(() => {
		m.current && b(v && !m.current.querySelector("[role=dialog]"));
	}, [m, v]), (0, x.useEffect)(() => {
		y && i.trigger !== "PreviewTrigger" && (i.trigger !== "SubmenuTrigger" || Jn() !== "pointer") && m.current && !Lt(m.current) && ir(m.current);
	}, [
		y,
		m,
		i.trigger
	]);
	let S = (0, x.useMemo)(() => {
		let e = _.children;
		if (r) for (let t of r) e = /*#__PURE__*/ x.createElement(t.Provider, { value: null }, e);
		return e;
	}, [_.children, r]), [C, w] = (0, x.useState)(null), T = (0, x.useCallback)(() => {
		i.triggerRef.current && w(i.triggerRef.current.getBoundingClientRect().width + "px");
	}, [i.triggerRef]);
	V(T, [T]), Nc({
		ref: _.style?.["--trigger-width"] ? void 0 : i.triggerRef,
		onResize: T
	});
	let E = {
		...l.style,
		"--trigger-anchor-point": p ? `${p.x}px ${p.y}px` : void 0,
		..._.style,
		"--trigger-width": _.style?.["--trigger-width"] || C
	}, D = /*#__PURE__*/ x.createElement(Xf.div, {
		...H(U(i, { global: !0 }), l),
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
	}, !i.isNonModal && /*#__PURE__*/ x.createElement(gl, { onDismiss: e.close }), /*#__PURE__*/ x.createElement(Gm.Provider, { value: {
		...d,
		placement: f,
		ref: a
	} }, S), /*#__PURE__*/ x.createElement(gl, { onDismiss: e.close }));
	return c ? /*#__PURE__*/ x.createElement(fc, {
		...i,
		shouldContainFocus: y && i.trigger !== "PreviewTrigger",
		isExiting: t,
		portalContainer: n ?? s?.current ?? void 0
	}, D) : /*#__PURE__*/ x.createElement(fc, {
		...i,
		shouldContainFocus: y && i.trigger !== "PreviewTrigger",
		isExiting: t,
		portalContainer: n
	}, !i.isNonModal && e.isOpen && /*#__PURE__*/ x.createElement("div", {
		"data-testid": "underlay",
		...u,
		style: {
			position: "fixed",
			inset: 0
		}
	}), /*#__PURE__*/ x.createElement("div", {
		ref: o,
		style: { display: "contents" }
	}, /*#__PURE__*/ x.createElement(Zm.Provider, { value: o }, D)));
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Dialog.mjs
var eh = /*#__PURE__*/ (0, x.createContext)(null), th = /*#__PURE__*/ (0, x.createContext)(null), nh = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let n = e["aria-labelledby"];
	[e, t] = Gf(e, t, eh);
	let { dialogProps: r, titleProps: i, contentProps: a } = mc({
		...e,
		"aria-labelledby": n
	}, t), o = (0, x.useContext)(th);
	!r["aria-label"] && !r["aria-labelledby"] && e["aria-labelledby"] && (r["aria-labelledby"] = e["aria-labelledby"]);
	let s = Uf({
		defaultClassName: "react-aria-Dialog",
		className: e.className,
		style: e.style,
		children: e.children,
		values: { close: o?.close || (() => {}) }
	}), c = U(e, { global: !0 });
	return /*#__PURE__*/ x.createElement(Xf.section, {
		...H(c, s, r),
		render: e.render,
		ref: t,
		slot: e.slot || void 0
	}, /*#__PURE__*/ x.createElement(Hf, { values: [
		[dp, { slots: {
			[Vf]: {},
			title: {
				...i,
				level: 2
			}
		} }],
		[pp, { slots: {
			[Vf]: {},
			description: a
		} }],
		[sp, { slots: {
			[Vf]: {},
			close: { onPress: () => o?.close() }
		} }]
	] }, s.children));
}), rh = typeof document < "u" && window.visualViewport;
function ih() {
	let e = An(), [t, n] = (0, x.useState)(() => e ? {
		width: 0,
		height: 0
	} : ah());
	return (0, x.useEffect)(() => {
		let e = (e) => {
			n((t) => e.width === t.width && e.height === t.height ? t : e);
		}, t = () => {
			rh && rh.scale > 1 || e(ah());
		}, r, i = (t) => {
			rh && rh.scale > 1 || _i(z(t)) && (r = requestAnimationFrame(() => {
				let t = Ft();
				(!t || !_i(t)) && e({
					width: document.documentElement.clientWidth,
					height: document.documentElement.clientHeight
				});
			}));
		};
		return e(ah()), an() && sn() && window.addEventListener("blur", i, !0), rh ? rh.addEventListener("resize", t) : window.addEventListener("resize", t), () => {
			cancelAnimationFrame(r), an() && sn() && window.removeEventListener("blur", i, !0), rh ? rh.removeEventListener("resize", t) : window.removeEventListener("resize", t);
		};
	}, []), t;
}
function ah() {
	return {
		width: rh ? Math.min(rh.width * rh.scale, document.documentElement.clientWidth) : document.documentElement.clientWidth,
		height: rh ? rh.height * rh.scale : document.documentElement.clientHeight
	};
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Modal.mjs
var oh = /*#__PURE__*/ (0, x.createContext)(null), sh = /*#__PURE__*/ (0, x.createContext)(null), ch = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	if ((0, x.useContext)(sh)) return /*#__PURE__*/ x.createElement(fh, {
		...e,
		modalRef: t
	}, e.children);
	let { isDismissable: n, isKeyboardDismissDisabled: r, isOpen: i, defaultOpen: a, onOpenChange: o, children: s, isEntering: c, isExiting: l, UNSTABLE_portalContainer: u, shouldCloseOnInteractOutside: d, ...f } = e;
	return /*#__PURE__*/ x.createElement(uh, {
		isDismissable: n,
		isKeyboardDismissDisabled: r,
		isOpen: i,
		defaultOpen: a,
		onOpenChange: o,
		isEntering: c,
		isExiting: l,
		UNSTABLE_portalContainer: u,
		shouldCloseOnInteractOutside: d
	}, /*#__PURE__*/ x.createElement(fh, {
		...f,
		modalRef: t
	}, s));
});
function lh(e, t) {
	[e, t] = Gf(e, t, oh);
	let n = (0, x.useContext)(th), r = Km(e), i = e.isOpen != null || e.defaultOpen != null || !n ? r : n, a = Nr(t), o = (0, x.useRef)(null), s = Jm(a, i.isOpen), c = Jm(o, i.isOpen), l = s || c || e.isExiting || !1, u = An();
	return !i.isOpen && !l || u ? null : /*#__PURE__*/ x.createElement(dh, {
		...e,
		state: i,
		isExiting: l,
		overlayRef: a,
		modalRef: o
	});
}
var uh = /*#__PURE__*/ (0, x.forwardRef)(lh);
function dh({ UNSTABLE_portalContainer: e, ...t }) {
	let n = t.modalRef, { state: r } = t, { modalProps: i, underlayProps: a } = Dl(t, r, n), o = qm(t.overlayRef) || t.isEntering || !1, s = Uf({
		...t,
		defaultClassName: "react-aria-ModalOverlay",
		values: {
			isEntering: o,
			isExiting: t.isExiting,
			state: r
		}
	}), c = ih(), l, u;
	if (typeof document < "u") {
		let e = eo(document.body) ? document.body : document.scrollingElement || document.documentElement, t = e.getBoundingClientRect().width % 1, n = e.getBoundingClientRect().height % 1;
		l = e.scrollWidth - t, u = e.scrollHeight - n;
	}
	let d = {
		...s.style,
		"--visual-viewport-width": c.width + "px",
		"--visual-viewport-height": c.height + "px",
		"--page-width": l === void 0 ? void 0 : l + "px",
		"--page-height": u === void 0 ? void 0 : u + "px"
	};
	return /*#__PURE__*/ x.createElement(fc, {
		isExiting: t.isExiting,
		portalContainer: e
	}, /*#__PURE__*/ x.createElement(Xf.div, {
		...H(U(t, { global: !0 }), a),
		...s,
		style: d,
		ref: t.overlayRef,
		"data-entering": o || void 0,
		"data-exiting": t.isExiting || void 0
	}, /*#__PURE__*/ x.createElement(Hf, { values: [[sh, {
		modalProps: i,
		modalRef: n,
		isExiting: t.isExiting,
		isDismissable: t.isDismissable
	}], [th, r]] }, s.children)));
}
function fh(e) {
	let { modalProps: t, modalRef: n, isExiting: r, isDismissable: i } = (0, x.useContext)(sh), a = (0, x.useContext)(th), o = Nr((0, x.useMemo)(() => mr(e.modalRef, n), [e.modalRef, n])), s = qm(o), c = Uf({
		...e,
		defaultClassName: "react-aria-Modal",
		values: {
			isEntering: s,
			isExiting: r,
			state: a
		}
	});
	return /*#__PURE__*/ x.createElement(Xf.div, {
		...H(U(e, { global: !0 }), t),
		...c,
		ref: o,
		"data-entering": s || void 0,
		"data-exiting": r || void 0
	}, i && /*#__PURE__*/ x.createElement(gl, { onDismiss: a.close }), c.children);
}
//#endregion
//#region node_modules/react-stately/dist/private/radio/useRadioGroupState.mjs
var ph = Math.round(Math.random() * 1e10), mh = 0;
function hh(e) {
	let t = (0, x.useMemo)(() => e.name || `radio-group-${ph}-${++mh}`, [e.name]), [n, r] = Fo(e.value, e.defaultValue ?? null, e.onChange), [i] = (0, x.useState)(n), [a, o] = (0, x.useState)(null), s = So({
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
var gh = /*#__PURE__*/ (0, x.createContext)(null), _h = /*#__PURE__*/ (0, x.createContext)(null), vh = /*#__PURE__*/ (0, x.createContext)(null), yh = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	[e, t] = Gf(e, t, gh);
	let { validationBehavior: n } = Wf(gp) || {}, r = e.validationBehavior ?? n ?? "native", i = hh({
		...e,
		validationBehavior: r
	}), [a, o] = Kf(!e["aria-label"] && !e["aria-labelledby"]), { radioGroupProps: s, labelProps: c, descriptionProps: l, errorMessageProps: u, ...d } = ru({
		...e,
		label: o,
		validationBehavior: r
	}, i), f = Uf({
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
	}), p = U(e, { global: !0 });
	return /*#__PURE__*/ x.createElement(Xf.div, {
		...H(p, f, s),
		ref: t,
		slot: e.slot || void 0,
		"data-orientation": e.orientation || "vertical",
		"data-invalid": i.isInvalid || void 0,
		"data-disabled": i.isDisabled || void 0,
		"data-readonly": i.isReadOnly || void 0,
		"data-required": i.isRequired || void 0
	}, /*#__PURE__*/ x.createElement(Hf, { values: [
		[vh, i],
		[ip, {
			...c,
			ref: a,
			elementType: "span"
		}],
		[pp, { slots: {
			description: l,
			errorMessage: u
		} }],
		[hp, d]
	] }, /*#__PURE__*/ x.createElement(gm, null, f.children)));
}), bh = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { inputRef: n = null, ...r } = e;
	[e, t] = Gf(r, t, _h);
	let i = x.useContext(vh), a = Nr((0, x.useMemo)(() => mr(n, e.inputRef === void 0 ? null : e.inputRef), [n, e.inputRef])), o = nu({
		...qf(e),
		children: typeof e.children == "function" || e.children
	}, i, a);
	return /*#__PURE__*/ x.createElement(xh.Provider, { value: {
		...o,
		inputRef: a,
		defaultClassName: "react-aria-Radio"
	} }, /*#__PURE__*/ x.createElement(Sh, {
		...e,
		ref: t
	}));
}), xh = /*#__PURE__*/ (0, x.createContext)(null), Sh = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { labelProps: n, inputProps: r, isSelected: i, isDisabled: a, isPressed: o, defaultClassName: s, inputRef: c } = (0, x.useContext)(xh), l = x.useContext(vh), { isFocused: u, isFocusVisible: d, focusProps: f } = hc(), p = a || l.isReadOnly, { hoverProps: m, isHovered: h } = Sc({
		...e,
		isDisabled: p
	}), g = Uf({
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
	}), _ = U(e, { global: !0 });
	return delete _.id, delete _.onClick, /*#__PURE__*/ x.createElement(Xf.label, {
		...H(_, n, m, g),
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
	}, /*#__PURE__*/ x.createElement(Bo, { elementType: "span" }, /*#__PURE__*/ x.createElement("input", {
		...H(r, f),
		ref: c
	})), g.children);
});
//#endregion
//#region node_modules/react-stately/dist/private/select/useSelectState.mjs
function Ch(e) {
	let { selectionMode: t = "single", shouldCloseOnSelect: n = t === "single" } = e, r = Km(e), [i, a] = (0, x.useState)(null), o = (0, x.useMemo)(() => e.defaultValue === void 0 ? t === "single" ? e.defaultSelectedKey ?? null : [] : e.defaultValue, [
		e.defaultValue,
		e.defaultSelectedKey,
		t
	]), [s, c] = Fo((0, x.useMemo)(() => e.value === void 0 ? t === "single" ? e.selectedKey : void 0 : e.value, [
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
	}, d = jm({
		...e,
		selectionMode: t,
		disallowEmptySelection: t === "single",
		allowDuplicateSelectionEvents: !0,
		selectedKeys: (0, x.useMemo)(() => wh(l), [l]),
		onSelectionChange: (e) => {
			if (e !== "all") {
				if (t === "single") {
					let t = e.values().next().value ?? null;
					u(t);
				} else u([...e]);
				n && r.close(), m.commitValidation();
			}
		}
	}), f = d.selectionManager.firstSelectedKey, p = (0, x.useMemo)(() => [...d.selectionManager.selectedKeys].map((e) => d.collection.getItem(e)).filter((e) => e != null), [d.selectionManager.selectedKeys, d.collection]), m = So({
		...e,
		value: Array.isArray(l) && l.length === 0 ? null : l
	}), [h, g] = (0, x.useState)(!1), [_] = (0, x.useState)(l);
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
function wh(e) {
	if (e !== void 0) return e === null ? [] : Array.isArray(e) ? e : [e];
}
//#endregion
//#region node_modules/react-aria-components/dist/private/Select.mjs
function Th(e) {
	return e && e.__esModule ? e.default : e;
}
var Eh = /*#__PURE__*/ (0, x.createContext)(null), Dh = /*#__PURE__*/ (0, x.createContext)(null), Oh = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, Eh);
	let { children: n, isDisabled: r = !1, isInvalid: i = !1, isRequired: a = !1 } = e, o = (0, x.useMemo)(() => typeof n == "function" ? n({
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
	return /*#__PURE__*/ x.createElement(Xr, { content: o }, (n) => /*#__PURE__*/ x.createElement(Ah, {
		props: e,
		collection: n,
		selectRef: t
	}));
}), kh = [
	ip,
	sp,
	pp
];
function Ah({ props: e, selectRef: t, collection: n }) {
	let { validationBehavior: r } = Wf(gp) || {}, i = e.validationBehavior ?? r ?? "native", a = Ch({
		...e,
		collection: n,
		children: void 0,
		validationBehavior: i
	}), { isFocusVisible: o, focusProps: s } = hc({ within: !0 }), c = (0, x.useRef)(null), [l, u] = Kf(!e["aria-label"] && !e["aria-labelledby"]), { labelProps: d, triggerProps: f, valueProps: p, menuProps: m, descriptionProps: h, errorMessageProps: g, hiddenSelectProps: _, ...v } = au({
		...qf(e),
		label: u,
		validationBehavior: i
	}, a, c), y = (0, x.useMemo)(() => ({
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
	]), b = Uf({
		...e,
		values: y,
		defaultClassName: "react-aria-Select"
	}), S = U(e, { global: !0 });
	delete S.id;
	let C = (0, x.useRef)(null);
	return /*#__PURE__*/ x.createElement(Hf, { values: [
		[Eh, e],
		[Dh, a],
		[jh, p],
		[ip, {
			...d,
			ref: l,
			elementType: "span"
		}],
		[sp, {
			...f,
			ref: c,
			isPressed: a.isOpen,
			autoFocus: e.autoFocus
		}],
		[th, a],
		[Xm, {
			trigger: "Select",
			triggerRef: c,
			scrollRef: C,
			placement: "bottom start",
			"aria-labelledby": m["aria-labelledby"],
			clearContexts: kh
		}],
		[Fm, {
			...m,
			ref: C
		}],
		[Im, a],
		[pp, { slots: {
			description: h,
			errorMessage: g
		} }],
		[hp, v]
	] }, /*#__PURE__*/ x.createElement(Xf.div, {
		...H(S, b, s),
		ref: t,
		slot: e.slot || void 0,
		"data-focused": a.isFocused || void 0,
		"data-focus-visible": o || void 0,
		"data-open": a.isOpen || void 0,
		"data-disabled": e.isDisabled || void 0,
		"data-invalid": v.isInvalid || void 0,
		"data-required": e.isRequired || void 0
	}, b.children, /*#__PURE__*/ x.createElement(su, {
		..._,
		autoComplete: e.autoComplete
	})));
}
var jh = /*#__PURE__*/ (0, x.createContext)(null), Mh = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, jh);
	let n = (0, x.useContext)(Dh), { placeholder: r } = Wf(Eh), i = n.selectedItems.map((e) => {
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
	}), a = gc(), o = (0, x.useMemo)(() => n.selectedItems.map((e) => e?.textValue), [n.selectedItems]), s = n.selectionManager.selectionMode, c = (0, x.useMemo)(() => s === "single" ? o[0] ?? "" : a.format(o), [
		s,
		a,
		o
	]), l = (0, x.useMemo)(() => {
		if (s === "single") return i[0];
		let e = a.formatToParts(o);
		if (e.length === 0) return null;
		let t = 0;
		return e.map((e) => e.type === "element" ? /*#__PURE__*/ x.createElement(x.Fragment, { key: t }, i[t++]) : e.value);
	}, [
		s,
		a,
		o,
		i
	]), u = Ki(Th(cm), "react-aria-components"), d = Uf({
		...e,
		defaultChildren: l ?? r ?? u.format("selectPlaceholder"),
		defaultClassName: "react-aria-SelectValue",
		values: {
			selectedItem: n.selectedItems[0]?.value ?? null,
			selectedItems: (0, x.useMemo)(() => n.selectedItems.map((e) => e.value ?? null), [n.selectedItems]),
			selectedText: c,
			isPlaceholder: n.selectedItems.length === 0,
			state: n
		}
	}), f = U(e, { global: !0 });
	return /*#__PURE__*/ x.createElement(Xf.span, {
		ref: t,
		...f,
		...d,
		"data-placeholder": n.selectedItems.length === 0 || void 0
	}, /*#__PURE__*/ x.createElement(pp.Provider, { value: void 0 }, d.children));
}), Nh = /*#__PURE__*/ (0, x.createContext)(null), Ph = /*#__PURE__*/ (0, x.createContext)(null), Fh = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { inputRef: n = null, ...r } = e;
	[e, t] = Gf(r, t, Nh);
	let i = Nr((0, x.useMemo)(() => mr(n, e.inputRef === void 0 ? null : e.inputRef), [n, e.inputRef])), a = Io(e), o = cu({
		...qf(e),
		children: typeof e.children == "function" || e.children
	}, a, i);
	return /*#__PURE__*/ x.createElement(Hf, { values: [[Ph, a], [Ih, {
		...o,
		inputRef: i,
		defaultClassName: "react-aria-Switch"
	}]] }, /*#__PURE__*/ x.createElement(Lh, {
		...e,
		ref: t
	}));
}), Ih = /*#__PURE__*/ (0, x.createContext)(null), Lh = /*#__PURE__*/ (0, x.forwardRef)(function(e, t) {
	let { labelProps: n, inputProps: r, isSelected: i, isDisabled: a, isReadOnly: o, isPressed: s, isInvalid: c, inputRef: l, defaultClassName: u, isRequired: d } = (0, x.useContext)(Ih), { isFocused: f, isFocusVisible: p, focusProps: m } = hc(), h = a || o, g = (0, x.useContext)(Ph), { hoverProps: _, isHovered: v } = Sc({
		...e,
		isDisabled: h
	}), y = Uf({
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
	}), b = U(e, { global: !0 });
	return delete b.id, delete b.onClick, /*#__PURE__*/ x.createElement(Xf.label, {
		...H(b, n, _, y),
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
	}, /*#__PURE__*/ x.createElement(Bo, { elementType: "span" }, /*#__PURE__*/ x.createElement("input", {
		...H(r, m),
		ref: l
	})), y.children);
}), Rh = /*#__PURE__*/ (0, x.createContext)({}), zh = /*#__PURE__*/ (0, x.createContext)(null), Bh = /*#__PURE__*/ Br(function(e, t) {
	[e, t] = Gf(e, t, zh);
	let { validationBehavior: n } = Wf(gp) || {}, r = e.validationBehavior ?? n ?? "native", i = (0, x.useRef)(null);
	[e, i] = Gf(e, i, Qf);
	let [a, o] = Kf(!e["aria-label"] && !e["aria-labelledby"]), [s, c] = (0, x.useState)("input"), { labelProps: l, inputProps: u, descriptionProps: d, errorMessageProps: f, ...p } = Vo({
		...qf(e),
		inputElementType: s,
		label: o,
		validationBehavior: r
	}, i), m = (0, x.useCallback)((e) => {
		i.current = e, e && c(e instanceof HTMLTextAreaElement ? "textarea" : "input");
	}, [i]), h = Uf({
		...e,
		values: {
			isDisabled: e.isDisabled || !1,
			isInvalid: p.isInvalid,
			isReadOnly: e.isReadOnly || !1,
			isRequired: e.isRequired || !1
		},
		defaultClassName: "react-aria-TextField"
	}), g = U(e, { global: !0 });
	return delete g.id, /*#__PURE__*/ x.createElement(Xf.div, {
		...g,
		...h,
		ref: t,
		slot: e.slot || void 0,
		"data-disabled": e.isDisabled || void 0,
		"data-invalid": p.isInvalid || void 0,
		"data-readonly": e.isReadOnly || void 0,
		"data-required": e.isRequired || void 0
	}, /*#__PURE__*/ x.createElement(Hf, { values: [
		[ip, {
			...l,
			ref: a
		}],
		[Tp, {
			...u,
			ref: m
		}],
		[Rh, {
			...u,
			ref: m
		}],
		[Cp, {
			role: "presentation",
			isInvalid: p.isInvalid,
			isDisabled: e.isDisabled || !1
		}],
		[pp, { slots: {
			description: d,
			errorMessage: f
		} }],
		[hp, p]
	] }, h.children));
}), Vh = sf({
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
function Hh({ variant: e = "primary", size: t = "medium", iconOnly: n = !1, leadingIcon: r, trailingIcon: i, children: a, className: o, type: s = "button", ref: c, ...l }) {
	return /* @__PURE__ */ (0, S.jsxs)("button", {
		ref: c,
		type: s,
		className: of(Vh.base, Vh.size[t], Vh.variant[e], n && Vh.iconOnlySize[t], o),
		...l,
		children: [
			r ? /* @__PURE__ */ (0, S.jsx)(r, {
				className: Vh.icon[t],
				"aria-hidden": !0
			}) : null,
			!n && a != null && /* @__PURE__ */ (0, S.jsx)("span", {
				className: Vh.label[t],
				children: a
			}),
			!n && i ? /* @__PURE__ */ (0, S.jsx)(i, {
				className: Vh.icon[t],
				"aria-hidden": !0
			}) : null
		]
	});
}
//#endregion
//#region src/react/boardui/components/base/buttons/icon-button.tsx
var Uh = sf({
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
function Wh({ icon: e, size: t = "medium", className: n, type: r = "button", ref: i, ...a }) {
	return /* @__PURE__ */ (0, S.jsx)("button", {
		ref: i,
		type: r,
		className: of(Uh.base, Uh.size[t], n),
		...a,
		children: /* @__PURE__ */ (0, S.jsx)(e, {
			className: Uh.icon[t],
			"aria-hidden": !0
		})
	});
}
//#endregion
//#region src/react/boardui/components/base/input/label.tsx
function Gh({ isRequired: e = !1, isInvalid: t, tooltip: n, className: r, children: i, ...a }) {
	return /* @__PURE__ */ (0, S.jsxs)(ap, {
		"data-label": "true",
		...a,
		className: of("flex cursor-default items-center gap-0.5", "text-body-medium text-text-primary", r),
		children: [
			i,
			e && /* @__PURE__ */ (0, S.jsx)("span", {
				"aria-hidden": "true",
				className: "text-body-medium text-text-error-primary",
				children: "*"
			}),
			n && /* @__PURE__ */ (0, S.jsx)(wu, {
				className: "size-4 shrink-0 text-foreground-icon-quaternary",
				"aria-hidden": !0
			})
		]
	});
}
//#endregion
//#region src/react/boardui/components/base/input/hint-text.tsx
function Kh({ isInvalid: e = !1, className: t, ...n }) {
	return /* @__PURE__ */ (0, S.jsx)(mp, {
		slot: e ? "errorMessage" : "description",
		...n,
		className: of("pt-px text-caption-1-medium text-text-secondary", e && "text-text-error-primary", t)
	});
}
//#endregion
//#region src/react/boardui/components/base/input/input.tsx
var qh = (0, x.createContext)({});
function Jh({ size: e = "medium", fieldClassName: t, inputClassName: n, className: r, children: i, ...a }) {
	return /* @__PURE__ */ (0, S.jsx)(qh.Provider, {
		value: {
			size: e,
			fieldClassName: t,
			inputClassName: n
		},
		children: /* @__PURE__ */ (0, S.jsx)(Bh, {
			...a,
			"data-input-size": e,
			className: of("group flex h-max w-full flex-col items-start gap-1", r),
			children: i
		})
	});
}
Jh.displayName = "TextField";
var Yh = sf({
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
function Xh({ size: e, leadingIcon: t, trailingIcon: n, leadingAddon: r, fieldClassName: i, className: a, ref: o, groupRef: s, ...c }) {
	let l = (0, x.useContext)(qh), u = e ?? l.size ?? "medium", d = r != null;
	return /* @__PURE__ */ (0, S.jsx)(wp, {
		ref: s,
		className: ({ isFocusWithin: e, isHovered: t, isDisabled: n, isInvalid: r }) => of(Yh.field, d ? Yh.fieldWithAddonSize[u] : Yh.fieldSize[u], t && !e && !n && !r && "ring-border-button-hover", e && !n && !r && "ring-border-button-active", n && "bg-input-disabled-background text-input-disabled-foreground", r && "bg-background-tertiary-error text-foreground-icon-error", l.fieldClassName, i),
		children: /* @__PURE__ */ (0, S.jsxs)("div", {
			className: Yh.content,
			children: [/* @__PURE__ */ (0, S.jsxs)("div", {
				className: Yh.leftSection,
				children: [d ? r : t ? /* @__PURE__ */ (0, S.jsx)(t, {
					className: Yh.icon,
					"aria-hidden": !0
				}) : null, /* @__PURE__ */ (0, S.jsx)(Dp, {
					ref: o,
					...c,
					className: of(Yh.input, l.inputClassName, a)
				})]
			}), n ? /* @__PURE__ */ (0, S.jsx)(n, {
				className: Yh.icon,
				"aria-hidden": !0
			}) : null]
		})
	});
}
Xh.displayName = "InputBase";
function Zh({ label: e, hint: t, tooltip: n, placeholder: r, leadingIcon: i, trailingIcon: a, leadingAddon: o, fieldClassName: s, ref: c, groupRef: l, className: u, ...d }) {
	return /* @__PURE__ */ (0, S.jsx)(Jh, {
		...d,
		className: u,
		"aria-label": d["aria-label"] ?? (!e && typeof r == "string" ? r : void 0),
		children: ({ isRequired: u, isInvalid: d }) => /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [
			e && /* @__PURE__ */ (0, S.jsx)(Gh, {
				isRequired: u,
				isInvalid: d,
				tooltip: n,
				children: e
			}),
			/* @__PURE__ */ (0, S.jsx)(Xh, {
				ref: c,
				groupRef: l,
				placeholder: r,
				leadingIcon: i,
				trailingIcon: a,
				leadingAddon: o,
				fieldClassName: s
			}),
			t && /* @__PURE__ */ (0, S.jsx)(Kh, {
				isInvalid: d,
				children: t
			})
		] })
	});
}
Zh.displayName = "Input";
//#endregion
//#region src/react/settings/use-action.ts
function Qh(e = "") {
	let t = (0, x.useRef)(null), [n, r] = (0, x.useState)(""), [i, a] = (0, x.useState)(e);
	(0, x.useEffect)(() => () => t.current?.abort(), []);
	async function o(e, n, i, o) {
		if (t.current) return;
		let s = new AbortController();
		t.current = s, r(e), a("");
		try {
			let e = await n(s.signal);
			s.signal.aborted || i(e);
		} catch (e) {
			if (s.signal.aborted) return;
			o ? o(e) : a(ff(e));
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
function $h(e) {
	return e ? {
		"aria-busy": !0,
		"aria-disabled": !0
	} : {};
}
//#endregion
//#region src/react/avatar-picker/avatar-picker.ts
var eg = "/api/avatar-choices", tg = "/api/avatar-pick", ng = "/avatar-choice", rg = (e, t) => [
	"avatar-choices",
	e,
	t
], ig = (e, t) => `?kind=${encodeURIComponent(e)}&id=${t}`, ag = (e, t, n) => `${ng}${ig(e, t)}&ref=${encodeURIComponent(n)}`, og = (e, t, n) => Q(eg + ig(e, t), n);
async function sg(e, t, n) {
	if (!("file" in n)) {
		await pf(tg, {
			kind: e,
			id: t,
			...n
		});
		return;
	}
	let r = n.file, i = await fetch(`${tg}${ig(e, t)}&name=${encodeURIComponent(r.name)}`, {
		method: "POST",
		credentials: "same-origin",
		body: r
	});
	if (i.ok) return;
	let a = await i.json().catch(() => null);
	throw new uf(a?.error || `请求失败（${i.status}）`, i.status, a);
}
function cg(e, t) {
	if (!t) return "正在找可用的图…";
	let n = t.matched_names.filter((t) => t !== e);
	return n.length ? `${e}：图库里按「${n.join("」「")}」找到的。` : t.choices.length ? `${e}：换上的那张留在本机，随时能换回来。` : `${e}：图库里没有这个名字，用下面两种方式换。`;
}
var lg = (e) => !!e && e.index_stale && !e.choices.some((e) => e.source === "gfriends"), ug = {
	gfriends: "图库",
	history: "用过的"
}, dg = (e) => `${ug[e.source] || e.source} · ${e.label}` + (e.width ? ` · ${e.width}×${e.height}` : "") + (e.found_by ? ` · 按「${e.found_by}」找到` : "");
//#endregion
//#region src/react/avatar-picker/avatar-picker-page.tsx
function fg({ kind: e, entityId: t, name: n, onPicked: r }) {
	let [i, a] = (0, x.useState)(!1);
	return /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)("span", {
		className: "absolute right-1 bottom-1",
		children: /* @__PURE__ */ (0, S.jsx)(Wh, {
			icon: pu,
			size: "small",
			"aria-haspopup": "dialog",
			"aria-label": `更换${n}的头像`,
			onClick: () => a(!0)
		})
	}), /* @__PURE__ */ (0, S.jsx)(uh, {
		isOpen: i,
		onOpenChange: a,
		isDismissable: !0,
		className: "fixed inset-0 z-50 flex items-center justify-center bg-scrim p-4",
		children: /* @__PURE__ */ (0, S.jsx)(ch, {
			className: "flex max-h-full w-full max-w-avatar-picker flex-col overflow-hidden rounded-2xl border border-separator-border bg-background-primary-default shadow-dropdown",
			children: /* @__PURE__ */ (0, S.jsx)(nh, {
				"aria-label": "更换头像",
				className: "flex min-h-0 flex-col outline-none",
				children: /* @__PURE__ */ (0, S.jsx)(pg, {
					kind: e,
					entityId: t,
					name: n,
					onPicked: r,
					close: () => a(!1)
				})
			})
		})
	})] });
}
function pg({ kind: e, entityId: t, name: n, onPicked: r, close: i }) {
	let a = (0, x.useRef)(null), [o, s] = (0, x.useState)(""), [c, l] = (0, x.useState)(""), u = rg(e, t), d = (0, x.useRef)(!1), f = ct({
		queryKey: u,
		queryFn: ({ signal: n }) => og(e, t, n),
		retryOnMount: !0
	});
	(0, x.useEffect)(() => () => {
		d.current && yf.removeQueries({ queryKey: rg(e, t) });
	}, [e, t]);
	let p = lt({
		mutationFn: (n) => sg(e, t, n),
		onSuccess: () => {
			d.current = !0, i(), r();
		}
	});
	function m(e) {
		let t = e.currentTarget, n = t.files?.[0];
		t.value = "", l(""), n && p.mutate({ file: n });
	}
	let h = f.data, g = h?.choices ?? [], _ = c || (p.error ? ff(p.error) : "") || (f.error ? ff(f.error) : "");
	return /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [
		/* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex shrink-0 items-start gap-4 p-5",
			children: [
				/* @__PURE__ */ (0, S.jsx)("span", {
					"aria-hidden": !0,
					className: "flex size-14 shrink-0 items-center justify-center rounded-2xl border border-separator-border bg-background-secondary-default text-foreground-icon-secondary",
					children: /* @__PURE__ */ (0, S.jsx)(Eu, { className: "size-6" })
				}),
				/* @__PURE__ */ (0, S.jsxs)("div", {
					className: "flex min-w-0 flex-1 flex-col gap-2",
					children: [
						/* @__PURE__ */ (0, S.jsxs)("div", {
							className: "flex flex-wrap items-center gap-2",
							children: [/* @__PURE__ */ (0, S.jsx)(fp, {
								slot: "title",
								className: "text-title-3-semibold text-text-primary",
								children: "更换头像"
							}), g.length ? /* @__PURE__ */ (0, S.jsxs)(lf, {
								color: "soft",
								children: [g.length, " 张可选"]
							}) : null]
						}),
						/* @__PURE__ */ (0, S.jsx)("p", {
							className: "text-body-2-regular text-text-secondary",
							children: cg(n, h)
						}),
						lg(h) ? /* @__PURE__ */ (0, S.jsx)(gf, {
							tone: "neutral",
							children: "图库索引还没取过，只能从用过的图里选。"
						}) : null,
						_ ? /* @__PURE__ */ (0, S.jsx)(gf, {
							tone: "error",
							children: _
						}) : null
					]
				}),
				/* @__PURE__ */ (0, S.jsx)(Wh, {
					icon: _u,
					size: "small",
					"aria-label": "关闭",
					onClick: i
				})
			]
		}),
		/* @__PURE__ */ (0, S.jsx)("div", {
			className: "flex min-h-0 flex-1 flex-col overflow-y-auto border-t border-separator-border px-5 pt-4",
			children: /* @__PURE__ */ (0, S.jsx)("div", {
				role: "listbox",
				"aria-label": "候选头像",
				className: "inline-grid grid-cols-3 content-start gap-2 sm:grid-cols-4",
				children: g.map((n) => /* @__PURE__ */ (0, S.jsxs)("button", {
					type: "button",
					role: "option",
					"data-avatar-choice": !0,
					"aria-selected": n.current,
					title: dg(n),
					...$h(p.isPending),
					onClick: () => {
						p.isPending || p.mutate({ ref: n.ref });
					},
					className: "relative flex cursor-pointer flex-col gap-1 overflow-hidden rounded-2lg border border-separator-border bg-background-secondary-default pb-1 text-center text-caption-1-regular text-text-secondary outline-none hover:border-border-button-hover hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring aria-selected:border-border-focus-ring aria-selected:text-text-primary aria-disabled:cursor-progress aria-disabled:opacity-60",
					children: [
						/* @__PURE__ */ (0, S.jsx)("img", {
							loading: "lazy",
							alt: "",
							src: ag(e, t, n.ref),
							className: "block w-full aspect-avatar-choice object-cover"
						}),
						/* @__PURE__ */ (0, S.jsx)("span", {
							className: "truncate px-1",
							children: n.label
						}),
						n.current ? /* @__PURE__ */ (0, S.jsx)("span", {
							className: "absolute top-1 left-1",
							children: /* @__PURE__ */ (0, S.jsx)(lf, {
								variant: "caption",
								color: "blue",
								children: "在用"
							})
						}) : null
					]
				}, n.ref))
			})
		}),
		/* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex shrink-0 flex-wrap items-center gap-3 border-t border-separator-border p-5",
			children: [
				/* @__PURE__ */ (0, S.jsx)(Hh, {
					variant: "secondary",
					onClick: () => a.current?.click(),
					...$h(p.isPending),
					children: "从本机选图片"
				}),
				/* @__PURE__ */ (0, S.jsx)("input", {
					ref: a,
					type: "file",
					accept: "image/png,image/jpeg",
					tabIndex: -1,
					"aria-hidden": !0,
					className: "hidden",
					onChange: m
				}),
				/* @__PURE__ */ (0, S.jsxs)("div", {
					className: "flex min-w-0 flex-1 items-center gap-2",
					children: [/* @__PURE__ */ (0, S.jsx)("div", {
						className: "min-w-0 flex-1",
						children: /* @__PURE__ */ (0, S.jsx)(Zh, {
							type: "url",
							"aria-label": "图片地址",
							placeholder: "https://…",
							value: o,
							onChange: s
						})
					}), /* @__PURE__ */ (0, S.jsx)(Hh, {
						disabled: !o.trim(),
						...$h(p.isPending),
						onClick: () => {
							p.isPending || p.mutate({ url: o.trim() });
						},
						children: "用这个地址"
					})]
				})
			]
		})
	] });
}
//#endregion
//#region src/react/library-processing/library-processing.ts
var mg = "/api/library-processing", hg = ["library-processing"], gg = (e) => Q(mg, e);
async function _g(e) {
	await yf.fetchQuery({
		queryKey: hg,
		queryFn: () => gg(e)
	});
}
var vg = 2e3, yg = 1e4, bg = "连接中断，正在重新读取处理进度";
function xg(e, t) {
	return e?.status === "running" ? vg : t ? yg : !1;
}
var Sg = {
	reading_local: "读取本地资料",
	querying_metadata: "查询外部资料",
	fetching_cover: "采集缺失封面",
	writing_candidates: "保存资料候选"
}, Cg = {
	querying_metadata: "没有资料",
	fetching_cover: "没有封面"
};
function wg(e) {
	let t = Object.entries(e).filter(([e, t]) => Cg[e] && t > 0).map(([e, t]) => `${Cg[e]} ${t} 部`);
	return t.length ? `外部来源${t.join("、")}，7 天内不再问。` : "";
}
function Tg(e) {
	let t = Sg[e.current_action || ""] || e.stage || "正在处理", n = e.waited_seconds ? ` · 已等待 ${e.waited_seconds} 秒` : "";
	return e.current_asset_name ? `当前：${e.current_asset_name} · ${t}${n}` : t + n;
}
function Eg(e) {
	let t = e.issue_preview || [];
	return t.length ? {
		label: e.issues_truncated ? `问题清单：共 ${e.issue_count || 0} 项，展开查看前 ${t.length} 项` : `问题清单：共 ${e.issue_count || 0} 项`,
		items: t.map((e, t) => ({
			key: `${e.asset_id ?? "source"}-${t}`,
			label: e.title || (e.asset_id ? `视频 ${e.asset_id}` : "媒体来源"),
			href: e.asset_id ? `/item/${e.asset_id}` : "",
			note: e.message,
			hint: e.path || ""
		})),
		footnote: e.issues_log ? `完整记录：${e.issues_log}` : ""
	} : null;
}
var Dg = "peach.library-processing.announced", Og = 120;
function kg(e, t, n) {
	if (e.status !== "complete") return;
	let r = !!e.job_id && !!e.completed_at && Date.now() / 1e3 - e.completed_at < Og;
	if (!(!n && !r)) {
		try {
			if (e.job_id && localStorage.getItem(Dg) === e.job_id) return;
			e.job_id && localStorage.setItem(Dg, e.job_id);
		} catch {}
		t(`扫描与资料采集已完成：识别 ${e.identified || 0} 个番号，整理 ${e.candidates || 0} 组资料候选`);
	}
}
//#endregion
//#region src/react/boardui/components/base/buttons/link-button.tsx
var Ag = sf({
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
function jg({ variant: e = "primary", size: t = "medium", leadingIcon: n, trailingIcon: r, children: i, className: a, disabled: o = !1, ...s }) {
	let c = of(Ag.base, Ag.size[t], Ag.variant[e], a), l = /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [
		n ? /* @__PURE__ */ (0, S.jsx)(n, {
			className: Ag.icon[t],
			"aria-hidden": !0
		}) : null,
		i != null && /* @__PURE__ */ (0, S.jsx)("span", { children: i }),
		r ? /* @__PURE__ */ (0, S.jsx)(r, {
			className: Ag.icon[t],
			"aria-hidden": !0
		}) : null
	] });
	if (s.href !== void 0) {
		let { ref: e, href: t, ...n } = s;
		return /* @__PURE__ */ (0, S.jsx)("a", {
			ref: e,
			href: o ? void 0 : t,
			"aria-disabled": o || void 0,
			className: c,
			...n,
			children: l
		});
	}
	let { ref: u, type: d = "button", ...f } = s;
	return /* @__PURE__ */ (0, S.jsx)("button", {
		ref: u,
		type: d,
		disabled: o,
		className: c,
		...f,
		children: l
	});
}
//#endregion
//#region src/react/boardui/components/base/dropdown/menu-styles.ts
var Mg = [
	"max-w-[calc(100vw-32px)] overflow-y-auto",
	"rounded-2xl border border-border-button-default bg-background-primary-default p-2.5 shadow-dropdown",
	"transition duration-150 ease-out",
	"data-[entering]:opacity-0 data-[entering]:scale-95 data-[entering]:blur-[2px]",
	"data-[exiting]:opacity-0 data-[exiting]:scale-95 data-[exiting]:blur-[2px]",
	"data-[placement=bottom]:origin-top-left data-[placement=top]:origin-bottom-left",
	"data-[placement=left]:origin-right data-[placement=right]:origin-left"
].join(" "), Ng = "w-[266px]", Pg = "flex w-full flex-col gap-1 outline-none", Fg = ["flex w-full cursor-pointer items-center gap-2 rounded-2lg p-2 text-left", "text-text-primary outline-none transition-colors"].join(" "), Ig = "hover:bg-dropdown-item-hover-background focus-visible:bg-dropdown-item-hover-background";
//#endregion
//#region src/react/boardui/components/application/settings/settings-rows.tsx
function Lg({ className: e, children: t }) {
	return /* @__PURE__ */ (0, S.jsx)("div", {
		className: of("flex w-full flex-col rounded-2xl bg-background-secondary-default pl-3", e),
		children: t
	});
}
function Rg({ className: e, children: t }) {
	return /* @__PURE__ */ (0, S.jsx)("p", {
		className: of("w-full px-3 text-body-2-medium text-text-secondary", e),
		children: t
	});
}
function zg({ label: e, description: t, children: n }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: of("flex min-h-[52px] w-full items-center justify-between gap-4 py-2.5 pr-2.5", "border-b border-separator-border last:border-b-0"),
		children: [/* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex min-w-0 flex-col",
			children: [/* @__PURE__ */ (0, S.jsx)("p", {
				className: "text-body-regular text-text-primary",
				children: e
			}), t && /* @__PURE__ */ (0, S.jsx)("p", {
				className: "text-body-2-regular text-text-secondary",
				children: t
			})]
		}), n]
	});
}
//#endregion
//#region src/react/settings/section.tsx
function Bg({ title: e, id: t, aside: n, onSubmit: r, children: i }) {
	let a = /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [n ? /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex w-full flex-wrap items-center justify-between gap-2",
		children: [/* @__PURE__ */ (0, S.jsx)("div", {
			className: "min-w-0 flex-1",
			children: /* @__PURE__ */ (0, S.jsx)(Rg, { children: e })
		}), n]
	}) : /* @__PURE__ */ (0, S.jsx)(Rg, { children: e }), /* @__PURE__ */ (0, S.jsx)(Lg, { children: i })] });
	return r ? /* @__PURE__ */ (0, S.jsx)("form", {
		id: t,
		"aria-label": e,
		noValidate: !0,
		onSubmit: r,
		className: "flex w-full flex-col gap-2",
		children: a
	}) : /* @__PURE__ */ (0, S.jsx)("section", {
		id: t,
		"aria-label": e,
		className: "flex w-full flex-col gap-2",
		children: a
	});
}
function Vg({ children: e }) {
	return /* @__PURE__ */ (0, S.jsx)("div", {
		className: "flex flex-col",
		children: e
	});
}
function Hg({ divided: e = !1, children: t }) {
	return e ? /* @__PURE__ */ (0, S.jsx)("div", {
		className: "flex flex-col gap-4 border-t border-separator-border py-4 pr-3",
		children: t
	}) : /* @__PURE__ */ (0, S.jsx)("div", {
		className: "flex flex-col gap-4 py-4 pr-3",
		children: t
	});
}
function Ug({ status: e, children: t }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex flex-wrap items-center justify-end gap-3 border-t border-separator-border py-3 pr-3",
		children: [e ? /* @__PURE__ */ (0, S.jsx)("div", {
			className: "mr-auto min-w-0 text-body-2-regular text-text-secondary",
			children: e
		}) : null, t]
	});
}
function Wg({ role: e, children: t }) {
	return /* @__PURE__ */ (0, S.jsx)("p", {
		role: e,
		className: "text-body-2-regular text-text-secondary",
		children: t
	});
}
function Gg({ children: e }) {
	return /* @__PURE__ */ (0, S.jsx)("p", {
		role: "alert",
		className: "text-body-2-regular text-text-error-primary",
		children: e
	});
}
function Kg({ children: e }) {
	return /* @__PURE__ */ (0, S.jsx)("p", {
		className: "text-body-medium text-text-primary",
		children: e
	});
}
function qg({ href: e, children: t }) {
	return /* @__PURE__ */ (0, S.jsx)(jg, {
		href: e,
		target: "_blank",
		rel: "noopener noreferrer",
		size: "small",
		trailingIcon: bu,
		children: t
	});
}
function Jg({ children: e }) {
	return /* @__PURE__ */ (0, S.jsx)("dl", {
		className: "flex flex-col",
		children: e
	});
}
function Yg({ term: e, children: t }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex min-h-11 items-center justify-between gap-4 border-b border-separator-border py-2.5 pr-3 last:border-b-0",
		children: [/* @__PURE__ */ (0, S.jsx)("dt", {
			className: "flex shrink-0 items-center gap-2 text-body-regular text-text-secondary",
			children: e
		}), /* @__PURE__ */ (0, S.jsx)("dd", {
			className: "flex min-w-0 flex-wrap items-center justify-end gap-2 text-right text-body-regular break-all text-text-primary",
			children: t
		})]
	});
}
function Xg({ summary: e, children: t }) {
	let n = (0, x.useId)(), r = (0, x.useRef)(null), i = (0, x.useRef)(null), [a, o] = (0, x.useState)(!1);
	return /* @__PURE__ */ (0, S.jsxs)("details", {
		ref: r,
		children: [/* @__PURE__ */ (0, S.jsxs)("summary", {
			"aria-expanded": a,
			"aria-controls": n,
			onClick: (e) => {
				e.preventDefault(), !(!r.current || !i.current) && (s(r.current, i.current, !a), o(!a));
			},
			className: "flex w-fit cursor-pointer list-none items-center gap-1 rounded-sm text-body-2-medium text-text-secondary outline-none select-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring",
			children: [/* @__PURE__ */ (0, S.jsx)(gu, {
				"aria-hidden": !0,
				className: a ? "size-4 shrink-0 rotate-90 transition-transform" : "size-4 shrink-0 transition-transform"
			}), e]
		}), /* @__PURE__ */ (0, S.jsx)("div", {
			ref: i,
			id: n,
			inert: !a,
			children: /* @__PURE__ */ (0, S.jsx)("div", {
				className: "flex flex-col gap-2 pt-3",
				children: t
			})
		})]
	});
}
function Zg({ name: e }) {
	return /* @__PURE__ */ (0, S.jsx)("svg", {
		"aria-hidden": !0,
		viewBox: "0 0 24 24",
		fill: "none",
		className: "size-4 shrink-0 stroke-current stroke-2",
		children: /* @__PURE__ */ (0, S.jsx)("use", { href: `#i-${e}` })
	});
}
function Qg({ mark: e }) {
	return e.startsWith("data:image/png;base64,") ? /* @__PURE__ */ (0, S.jsx)("img", {
		src: e,
		alt: "",
		width: 16,
		height: 16,
		className: "size-4 shrink-0"
	}) : /* @__PURE__ */ (0, S.jsx)(Zg, { name: e });
}
//#endregion
//#region src/react/library-processing/use-library-processing.ts
function $g({ toast: e, mode: t, monitor: n }) {
	let r = t === "notice" || !!n, i = ct({
		queryKey: hg,
		queryFn: ({ signal: e }) => gg(e),
		refetchInterval: (e) => xg(e.state.data, r)
	}), [a, o] = (0, x.useState)(null), s = (0, x.useRef)(void 0), c = i.data;
	return (0, x.useEffect)(() => {
		if (!c) return;
		let n = s.current;
		s.current = c.status;
		let r = n === "running" && c.status !== "running";
		r && o(c), (r || t === "notice") && kg(c, e, r);
	}, [
		c,
		t,
		e
	]), {
		job: i,
		settled: a,
		forget: () => o(null)
	};
}
//#endregion
//#region src/react/library-processing/library-processing-card.tsx
var e_ = [{
	label: "只扫描",
	icon: Su,
	command: { stage: "scan" }
}, {
	label: "只采集",
	icon: xu,
	command: { stage: "collect" }
}], t_ = of(Fg, Ig, "text-body-2-medium"), n_ = "扫描媒体文件夹，导入已有资料，采集缺失信息。两段也可以分开跑：新盘刚接上时先只扫描，几万个文件登记完就能用；采集被网络拖住时只重跑采集，不必再扫一遍磁盘。", r_ = "这个项目处理时间较长，暂时没有新进展。可以继续等待，或在任务结束后重试未完成项。", i_ = (e) => `已扫描 ${e.scanned || 0} 个文件，识别 ${e.identified || 0} 个番号，整理 ${e.candidates || 0} 组资料候选。`;
function a_({ busy: e, onRun: t }) {
	let n = (0, x.useRef)(null), [r, i] = (0, x.useState)(!1), a = (n) => {
		e || (i(!1), t(n));
	};
	return /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsxs)("span", {
		className: "flex items-center gap-1",
		children: [/* @__PURE__ */ (0, S.jsx)(Hh, {
			leadingIcon: vu,
			onClick: () => a({}),
			...$h(e),
			children: "扫描并补全资料"
		}), /* @__PURE__ */ (0, S.jsx)(Hh, {
			ref: n,
			iconOnly: !0,
			leadingIcon: mu,
			"aria-label": "更多扫描与采集方式",
			"aria-haspopup": "dialog",
			"aria-expanded": r,
			...$h(e),
			onClick: () => {
				e || i(!0);
			}
		})]
	}), /* @__PURE__ */ (0, S.jsx)(Qm, {
		triggerRef: n,
		isOpen: r,
		onOpenChange: i,
		placement: "bottom end",
		offset: 4,
		className: Mg,
		children: /* @__PURE__ */ (0, S.jsx)(nh, {
			"aria-label": "更多扫描与采集方式",
			className: "flex w-52 flex-col gap-1 outline-none",
			children: e_.map(({ label: e, icon: t, command: n }) => /* @__PURE__ */ (0, S.jsxs)("button", {
				type: "button",
				className: t_,
				onClick: () => a(n),
				children: [/* @__PURE__ */ (0, S.jsx)(t, {
					"aria-hidden": !0,
					className: "size-4 shrink-0"
				}), e]
			}, e))
		})
	})] });
}
function o_({ state: e, problem: t, settled: n, onRetry: r }) {
	let i = Eg(e), a = e.status === "failed" && !!e.retryable_asset_ids?.length, o = wg(e.notes || {});
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		"aria-live": "polite",
		className: "flex flex-col gap-4 empty:hidden",
		children: [
			e.status === "running" && e.stalled ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "warning",
				title: "处理较慢",
				children: r_
			}) : null,
			t || e.status === "failed" ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "error",
				extra: /* @__PURE__ */ (0, S.jsxs)("div", {
					className: "flex flex-col items-start gap-3 pt-1",
					children: [a ? /* @__PURE__ */ (0, S.jsx)(Hh, {
						variant: "secondary",
						size: "small",
						onClick: r,
						children: "重试未完成项"
					}) : null, i ? /* @__PURE__ */ (0, S.jsxs)(Xg, {
						summary: i.label,
						children: [/* @__PURE__ */ (0, S.jsx)("ul", {
							className: "flex max-h-96 flex-col gap-2 overflow-y-auto",
							children: i.items.map((e) => /* @__PURE__ */ (0, S.jsxs)("li", {
								className: "flex flex-col gap-0.5",
								children: [
									e.href ? /* @__PURE__ */ (0, S.jsx)("a", {
										href: e.href,
										className: "text-body-2-medium underline-offset-4 hover:underline",
										children: e.label
									}) : /* @__PURE__ */ (0, S.jsx)("span", {
										className: "text-body-2-medium",
										children: e.label
									}),
									/* @__PURE__ */ (0, S.jsx)("span", {
										className: "text-caption-1-regular",
										children: e.note
									}),
									e.hint ? /* @__PURE__ */ (0, S.jsx)("code", {
										className: "text-caption-1-regular break-all",
										children: e.hint
									}) : null
								]
							}, e.key))
						}), i.footnote ? /* @__PURE__ */ (0, S.jsx)("p", {
							className: "text-caption-1-regular break-all",
							children: i.footnote
						}) : null]
					}) : null]
				}),
				children: t || e.error || "处理未完成，请重试"
			}) : null,
			n?.status === "complete" ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "success",
				title: "处理完成",
				children: i_(n)
			}) : null,
			e.status !== "running" && o ? /* @__PURE__ */ (0, S.jsxs)(gf, {
				tone: "neutral",
				children: [o, e.issues_log ? ` 完整记录：${e.issues_log}` : ""]
			}) : null
		]
	});
}
function s_(e) {
	let { toast: t, onComplete: n } = e, { job: r, settled: i, forget: a } = $g(e), o = lt({
		mutationFn: (e) => pf(mg, e),
		onSuccess: (e) => {
			a(), yf.setQueryData(hg, e), yf.invalidateQueries({ queryKey: hg });
		}
	});
	(0, x.useEffect)(() => {
		i && n?.();
	}, [i, n]);
	let s = r.data ?? { status: "idle" }, c = o.error ? ff(o.error) : r.isError ? r.data ? bg : ff(r.error) : "", l = o.isPending || s.status === "running", u = s.status === "failed" && !!s.retryable_asset_ids?.length, d = Tg(s), f = (e) => {
		l || (o.reset(), o.mutate(e));
	};
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex flex-col gap-4",
		children: [/* @__PURE__ */ (0, S.jsxs)(Bg, {
			title: "扫描与采集",
			children: [/* @__PURE__ */ (0, S.jsxs)(Hg, { children: [/* @__PURE__ */ (0, S.jsx)("p", {
				className: "text-body-2-regular text-text-secondary",
				children: n_
			}), s.status === "running" ? /* @__PURE__ */ (0, S.jsx)("div", {
				className: "flex flex-col gap-1.5",
				children: s.total ? /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)(vf, {
					label: d,
					value: s.checked || 0,
					max: s.total
				}), /* @__PURE__ */ (0, S.jsxs)("p", {
					className: "text-caption-1-regular text-text-secondary",
					children: [
						d,
						" · ",
						s.checked || 0,
						" / ",
						s.total,
						" 个视频"
					]
				})] }) : /* @__PURE__ */ (0, S.jsx)(hf, { label: d })
			}) : null] }), /* @__PURE__ */ (0, S.jsxs)(Ug, { children: [
				/* @__PURE__ */ (0, S.jsx)(jg, {
					href: "/scraping",
					size: "small",
					trailingIcon: hu,
					children: "来源和凭证"
				}),
				s.candidates ? /* @__PURE__ */ (0, S.jsx)(jg, {
					href: "/review",
					size: "small",
					trailingIcon: hu,
					children: "复核资料"
				}) : null,
				u ? null : /* @__PURE__ */ (0, S.jsx)(a_, {
					busy: l,
					onRun: f
				})
			] })]
		}), /* @__PURE__ */ (0, S.jsx)(o_, {
			state: s,
			problem: c,
			settled: i,
			onRetry: () => {
				!s.job_id || !s.retryable_asset_ids?.length || f({
					job_id: s.job_id,
					retry: s.retryable_asset_ids
				});
			}
		})]
	});
}
//#endregion
//#region src/react/library-processing/library-processing-notice.tsx
var c_ = {
	gray: "flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-separator-border px-4 py-3 text-text-secondary",
	warning: "flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-separator-border bg-status-yellow-background px-4 py-3 text-status-yellow-text",
	error: "flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-separator-border bg-background-tertiary-error px-4 py-3 text-text-error-primary"
};
function l_({ value: e, max: t }) {
	let n = Math.max(0, Math.min(100, e / t * 100));
	return /* @__PURE__ */ (0, S.jsxs)("svg", {
		role: "progressbar",
		"aria-label": "任务完成率",
		"aria-valuemin": 0,
		"aria-valuemax": 100,
		"aria-valuenow": n,
		viewBox: "0 0 32 32",
		fill: "none",
		className: "size-6 shrink-0 -rotate-90 stroke-current",
		children: [/* @__PURE__ */ (0, S.jsx)("circle", {
			cx: "16",
			cy: "16",
			r: "13",
			strokeWidth: "4",
			className: "opacity-25"
		}), /* @__PURE__ */ (0, S.jsx)("circle", {
			cx: "16",
			cy: "16",
			r: "13",
			strokeWidth: "4",
			pathLength: 100,
			strokeDasharray: `${n} 100`,
			strokeLinecap: "round"
		})]
	});
}
function u_(e) {
	let { job: t } = $g(e), n = t.data, r = t.isError ? n ? bg : ff(t.error) : "", i = n?.status ?? "idle", a = i === "failed", o = i === "running";
	if (!r && !o && !a) return null;
	let s = a ? "error" : r || n?.stalled ? "warning" : "gray", c = n?.checked || 0, l = n?.total || 0, u = r || (a ? "扫描与资料采集未完成" : Tg(n) + (l ? ` · ${c} / ${l}` : "")), d = s === "gray" ? Tu : yu;
	return /* @__PURE__ */ (0, S.jsxs)("aside", {
		role: a ? "alert" : "status",
		className: c_[s],
		children: [/* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex min-w-0 items-center gap-3",
			children: [o && l ? /* @__PURE__ */ (0, S.jsx)(l_, {
				value: c,
				max: l
			}) : /* @__PURE__ */ (0, S.jsx)(d, {
				"aria-hidden": !0,
				className: "size-5 shrink-0"
			}), /* @__PURE__ */ (0, S.jsx)("p", {
				className: "min-w-0 text-body-2-regular",
				children: u
			})]
		}), /* @__PURE__ */ (0, S.jsx)(jg, {
			href: "/data-cleanup#libraryProcessing",
			size: "small",
			trailingIcon: hu,
			children: r || a ? "查看并处理" : "查看进度"
		})]
	});
}
//#endregion
//#region src/react/quality-goals/quality-goals.ts
var d_ = "/api/quality-goals?limit=200", f_ = ["quality-goals"], p_ = (e) => Q(d_, e);
async function m_(e) {
	await yf.fetchQuery({
		queryKey: f_,
		queryFn: () => p_(e)
	});
}
var h_ = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
//#endregion
//#region src/react/quality-goals/quality-goals-page.tsx
function g_({ item: r, openItem: i, javTitleHtml: a, javDisplayName: o, srcBadge: s }) {
	let c = () => i(r.id);
	return /* @__PURE__ */ (0, S.jsxs)("li", {
		"data-goal-id": r.id,
		className: "flex min-w-0 flex-col gap-3 rounded-2xl border border-separator-border p-3",
		children: [/* @__PURE__ */ (0, S.jsxs)("div", {
			className: "flex min-w-0 gap-4",
			children: [/* @__PURE__ */ (0, S.jsxs)("button", {
				type: "button",
				onClick: c,
				"aria-label": `打开 ${o(r)}`,
				className: "relative inline-grid w-card-cover shrink-0 aspect-card-cover cursor-pointer place-items-center overflow-hidden rounded-lg bg-black",
				children: [/* @__PURE__ */ (0, S.jsx)("span", {
					className: "text-caption-1-regular text-text-tertiary",
					children: "暂无预览"
				}), /* @__PURE__ */ (0, S.jsx)("img", {
					src: h_(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove(),
					className: "absolute inset-0 size-full object-contain"
				})]
			}), /* @__PURE__ */ (0, S.jsxs)("div", {
				className: "flex min-w-0 flex-col gap-1.5",
				children: [
					/* @__PURE__ */ (0, S.jsx)("h3", {
						className: "text-title-1-medium text-text-primary",
						children: /* @__PURE__ */ (0, S.jsx)("button", {
							type: "button",
							"data-middle-truncate": !0,
							onClick: c,
							className: "block w-full cursor-pointer text-left",
							dangerouslySetInnerHTML: { __html: a(r) }
						})
					}),
					/* @__PURE__ */ (0, S.jsxs)("p", {
						className: "flex flex-wrap items-center gap-2 text-caption-1-regular text-text-secondary",
						children: [
							/* @__PURE__ */ (0, S.jsx)("span", {
								className: "contents",
								dangerouslySetInnerHTML: { __html: s(r.location, r.cost) }
							}),
							/* @__PURE__ */ (0, S.jsx)("span", { children: e[r.location] ?? r.location }),
							/* @__PURE__ */ (0, S.jsx)("span", { children: t(r.duration) }),
							/* @__PURE__ */ (0, S.jsx)("span", { children: n(r.size ?? 0) })
						]
					}),
					r.reason ? /* @__PURE__ */ (0, S.jsx)("p", {
						className: "text-caption-1-regular text-text-secondary",
						children: r.reason
					}) : null
				]
			})]
		}), /* @__PURE__ */ (0, S.jsx)("footer", {
			className: "flex justify-end",
			children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				variant: "secondary",
				size: "small",
				onClick: c,
				children: "查看版本"
			})
		})]
	});
}
function __(e) {
	let t = ct({
		queryKey: f_,
		queryFn: ({ signal: e }) => p_(e)
	}), n = t.data;
	if (!n) return /* @__PURE__ */ (0, S.jsx)(_f, { children: /* @__PURE__ */ (0, S.jsx)(gf, {
		tone: "error",
		title: "读取失败",
		children: t.error ? ff(t.error) : "读取高清版目标失败"
	}) });
	let r = n.items || [];
	return r.length ? /* @__PURE__ */ (0, S.jsxs)(_f, { children: [/* @__PURE__ */ (0, S.jsxs)("p", {
		className: "text-body-2-regular text-text-secondary",
		children: [
			/* @__PURE__ */ (0, S.jsx)("strong", {
				className: "text-title-2-semibold text-text-primary",
				children: "待升级"
			}),
			" · ",
			n.total,
			" 部作品"
		]
	}), /* @__PURE__ */ (0, S.jsx)("ul", {
		className: "card-grid gap-5",
		children: r.map((t) => /* @__PURE__ */ (0, S.jsx)(g_, {
			item: t,
			...e
		}, t.id))
	})] }) : /* @__PURE__ */ (0, S.jsx)(_f, { children: /* @__PURE__ */ (0, S.jsx)(mf, {
		icon: Du,
		title: "没有标记中的高清版目标",
		children: "现有版本都已满足条件，或还没有加入追踪。"
	}) });
}
//#endregion
//#region src/react/boardui/components/foundations/icons/chevrons.tsx
function v_(e) {
	return /* @__PURE__ */ (0, S.jsx)("svg", {
		viewBox: "0 0 16 16",
		fill: "none",
		"aria-hidden": !0,
		...e,
		children: /* @__PURE__ */ (0, S.jsx)("path", {
			d: "M4 7L7.29289 10.2929C7.68342 10.6834 8.31658 10.6834 8.70711 10.2929L12 7",
			stroke: "currentColor",
			strokeWidth: "2",
			strokeLinecap: "round"
		})
	});
}
//#endregion
//#region src/react/boardui/utils/use-dismiss-on-outside-press.ts
function y_(e, t, n) {
	(0, x.useEffect)(() => {
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
function b_(e, t) {
	let n = (0, x.useRef)(!1);
	return (0, x.useEffect)(() => {
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
var x_ = (0, x.createContext)("md");
function S_({ className: e, triggerClassName: t, popoverClassName: n, size: r = "md", children: i, items: a, renderValue: o, ref: s, ...c }) {
	let l = (0, x.useRef)(null), u = (0, x.useRef)(null), [d, f] = (0, x.useState)(!1);
	y_(d, () => f(!1), [l, u]);
	let p = b_(d, l);
	return /* @__PURE__ */ (0, S.jsx)(Oh, {
		ref: s,
		...c,
		isOpen: d,
		onOpenChange: (e) => p(e) && f(e),
		className: of("group flex flex-col", e),
		children: ({ isOpen: e }) => /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsxs)(cp, {
			ref: l,
			className: of("flex w-full cursor-pointer items-center justify-between rounded-2lg", "border border-border-button-default bg-background-primary-default shadow-xs", "text-text-primary", "transition-[background-color,border-color,box-shadow,padding,font-size] duration-200 ease", "hover:bg-background-primary-hover hover:border-border-button-hover", "outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus-ring", "disabled:cursor-not-allowed disabled:bg-background-primary-disabled disabled:text-text-tertiary disabled:shadow-none", r === "sm" ? "gap-1 px-[7px] py-1 text-body-2-medium" : "gap-1.5 px-2.5 py-2 text-body-medium", t),
			children: [/* @__PURE__ */ (0, S.jsx)(Mh, {
				className: of("flex min-w-0 items-center truncate", r === "sm" ? "gap-1" : "gap-[5px]"),
				children: o
			}), /* @__PURE__ */ (0, S.jsx)(v_, { className: of("shrink-0 text-text-secondary transition-transform duration-200 ease", r === "sm" ? "size-3.5" : "size-4", e && "rotate-180") })]
		}), /* @__PURE__ */ (0, S.jsx)(Qm, {
			ref: u,
			isNonModal: !0,
			offset: 4,
			className: of(Ng, Mg, "p-2", n),
			children: /* @__PURE__ */ (0, S.jsx)(Lm, {
				items: a,
				className: of(Pg, "max-h-[240px] overflow-auto"),
				children: /* @__PURE__ */ (0, S.jsx)(x_.Provider, {
					value: r,
					children: i
				})
			})
		})] })
	});
}
function C_({ className: e, children: t, ...n }) {
	let r = (0, x.useContext)(x_);
	return /* @__PURE__ */ (0, S.jsx)(Vm, {
		...n,
		className: (t) => of(Fg, r === "sm" ? "px-2 py-1.5 text-body-2-medium" : "text-body-medium", (t.isFocused || t.isSelected) && "bg-dropdown-item-hover-background", t.isDisabled && "cursor-not-allowed text-text-disabled", typeof e == "function" ? e(t) : e),
		children: t
	});
}
//#endregion
//#region src/react/scraping/scraping.ts
var w_ = "/api/scraping", T_ = "/api/scraping/settings", E_ = "/api/scraping/check", D_ = "/api/scraping/cover", O_ = ["scraping"], k_ = ["scraping", "cover"], A_ = 2e3, j_ = (e) => Q(w_, e), M_ = (e) => Q(D_, e);
async function N_(e) {
	await Promise.all([yf.fetchQuery({
		queryKey: O_,
		queryFn: () => j_(e)
	}), yf.fetchQuery({
		queryKey: k_,
		queryFn: () => M_(e)
	})]);
}
function P_(e, t) {
	return `${t}${e.label === "来源页面" ? "" : " 高清图片"}：${e.ok ? "可连接" : "不能连接"}` + (e.width ? ` · ${e.width} × ${e.height}` : "") + (e.message ? `。${e.message}` : "");
}
//#endregion
//#region src/react/scraping/scraping-page.tsx
var F_ = [["peach", "Peach 代理"], ["direct", "直接连接"]], I_ = [["paste", "粘贴 Cookie"], ["file", "导入文件"]];
function L_({ source: e }) {
	return /* @__PURE__ */ (0, S.jsx)("img", {
		src: i({ source: e }),
		alt: "",
		width: 16,
		height: 16,
		loading: "lazy",
		onError: (e) => e.currentTarget.remove(),
		className: "size-4 shrink-0 rounded-sm object-contain"
	});
}
function R_({ source: e, toast: t }) {
	let [n, r] = (0, x.useState)(e.network), [i, a] = (0, x.useState)(""), [o, s] = (0, x.useState)(""), [c, l] = (0, x.useState)(I_[0][0]), [u, d] = (0, x.useState)(""), [f, p] = (0, x.useState)(""), m = (0, x.useRef)(null);
	function h() {
		a(""), s(""), d(""), p(""), m.current && (m.current.value = "");
	}
	let g = lt({
		mutationFn: (t) => pf(T_, {
			source: e.source,
			network: n,
			cookie: i,
			cookies_text: o,
			revoke: t
		}),
		onSuccess: (e, n) => {
			yf.setQueryData(O_, (t) => t && {
				...t,
				sources: t.sources.map((t) => t.source === e.saved.source ? e.saved : t)
			}), h(), t(n ? "Cookie 已撤销" : "来源设置已保存");
		}
	}), _ = lt({ mutationFn: () => pf(E_, { source: e.source }) }), v = g.isPending || _.isPending, y = (e) => {
		e.preventDefault(), !v && (_.reset(), g.mutate(!1));
	}, b = () => {
		v || (_.reset(), g.mutate(!0));
	}, C = () => {
		v || (g.reset(), _.mutate());
	};
	async function w(e) {
		let t = e.currentTarget, n = t.files?.[0];
		if (s(""), p(""), !n) {
			d("");
			return;
		}
		if (n.size > 262144) {
			t.value = "", d(""), p("Cookie 文本超过 256 KiB");
			return;
		}
		try {
			let e = await n.text();
			s(e), d(n.name);
		} catch {
			p("Cookie 文件未读取，请重新选择");
		}
	}
	let T = f || (g.error ? ff(g.error) : "") || (_.error ? ff(_.error) : ""), E = _.data?.results ?? [], D = n === "peach" || e.accepts_cookie || !!T || E.length > 0;
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: e.label,
		onSubmit: y,
		aside: /* @__PURE__ */ (0, S.jsxs)("span", {
			className: "flex min-w-0 items-center gap-1",
			children: [/* @__PURE__ */ (0, S.jsx)(L_, { source: e.source }), /* @__PURE__ */ (0, S.jsx)(qg, {
				href: e.login,
				children: e.login
			})]
		}),
		children: [
			/* @__PURE__ */ (0, S.jsx)(Vg, { children: /* @__PURE__ */ (0, S.jsx)(zg, {
				label: "连接方式",
				children: /* @__PURE__ */ (0, S.jsx)(S_, {
					"aria-label": "连接方式",
					selectedKey: n,
					onSelectionChange: (e) => {
						e !== null && r(String(e));
					},
					children: F_.map(([e, t]) => /* @__PURE__ */ (0, S.jsx)(C_, {
						id: e,
						children: t
					}, e))
				})
			}) }),
			D ? /* @__PURE__ */ (0, S.jsxs)(Hg, {
				divided: !0,
				children: [
					n === "peach" ? /* @__PURE__ */ (0, S.jsx)("span", {
						className: "self-start",
						children: /* @__PURE__ */ (0, S.jsx)(jg, {
							href: "/configuration#peachProxy",
							size: "small",
							trailingIcon: hu,
							children: "配置 Peach 代理"
						})
					}) : null,
					e.accepts_cookie ? /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [
						/* @__PURE__ */ (0, S.jsx)("p", {
							className: "text-body-2-regular text-text-secondary",
							children: e.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。"
						}),
						/* @__PURE__ */ (0, S.jsx)(yh, {
							"aria-label": "提供 Cookie 的方式（二选一）",
							value: c,
							onChange: (e) => {
								l(e), h();
							},
							className: "flex flex-wrap gap-1",
							children: I_.map(([e, t]) => /* @__PURE__ */ (0, S.jsx)(bh, {
								value: e,
								className: "flex h-8 cursor-pointer items-center rounded-lg px-3 text-body-2-medium text-text-secondary outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-border-focus-ring data-selected:bg-background-tertiary-default data-selected:text-text-primary",
								children: t
							}, e))
						}),
						c === "paste" ? /* @__PURE__ */ (0, S.jsx)(Zh, {
							type: "password",
							label: "Cookie",
							autoComplete: "off",
							value: i,
							onChange: a
						}) : /* @__PURE__ */ (0, S.jsxs)("div", {
							className: "flex flex-col gap-2",
							children: [
								/* @__PURE__ */ (0, S.jsx)(Kg, { children: "Netscape Cookie 文件（.txt）" }),
								/* @__PURE__ */ (0, S.jsxs)("div", {
									className: "flex flex-wrap items-center gap-3",
									children: [/* @__PURE__ */ (0, S.jsx)(Hh, {
										variant: "secondary",
										onClick: () => m.current?.click(),
										children: "选择文件"
									}), /* @__PURE__ */ (0, S.jsx)("span", {
										className: "min-w-0 text-body-2-regular break-all text-text-secondary",
										children: u || "未选择文件"
									})]
								}),
								/* @__PURE__ */ (0, S.jsx)("input", {
									ref: m,
									type: "file",
									accept: ".txt",
									tabIndex: -1,
									"aria-hidden": !0,
									className: "hidden",
									onChange: (e) => {
										w(e);
									}
								})
							]
						})
					] }) : null,
					T ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: T }) : null,
					E.map((t) => /* @__PURE__ */ (0, S.jsx)(gf, {
						tone: t.ok ? "success" : "error",
						children: P_(t, e.label)
					}, t.label))
				]
			}) : null,
			/* @__PURE__ */ (0, S.jsxs)(Ug, { children: [
				e.accepts_cookie && e.cookie_saved ? /* @__PURE__ */ (0, S.jsx)(Hh, {
					variant: "secondary",
					onClick: b,
					...$h(v),
					children: "撤销 Cookie"
				}) : null,
				/* @__PURE__ */ (0, S.jsx)(Hh, {
					variant: "secondary",
					onClick: C,
					...$h(v),
					children: "检查连接"
				}),
				/* @__PURE__ */ (0, S.jsx)(Hh, {
					type: "submit",
					...$h(v),
					children: "保存"
				})
			] })
		]
	});
}
function z_({ toast: e }) {
	let [t, n] = (0, x.useState)(""), [r, i] = (0, x.useState)(!1), [a, o] = (0, x.useState)(null), s = ct({
		queryKey: k_,
		queryFn: ({ signal: e }) => M_(e),
		refetchInterval: (e) => e.state.data?.status === "running" && A_
	}), c = lt({
		mutationFn: () => pf(D_, { code: t }),
		onSuccess: () => {
			i(!0), o(null), yf.invalidateQueries({ queryKey: k_ });
		}
	}), l = (s.data?.status ?? "idle") === "running";
	(0, x.useEffect)(() => {
		let t = s.data;
		if (t) {
			if (t.status === "running") {
				r || i(!0);
				return;
			}
			r && (i(!1), o(t), t.status === "complete" && e(t.result || "封面采集完成"));
		}
	}, [
		s.data,
		r,
		e
	]);
	let u = (e) => {
		e.preventDefault(), !(l || c.isPending || !t.trim()) && c.mutate();
	}, d = c.error ? ff(c.error) : a?.status === "failed" ? a.error || "采集未取得" : "";
	return /* @__PURE__ */ (0, S.jsx)(Bg, {
		title: "高清封面",
		onSubmit: u,
		children: /* @__PURE__ */ (0, S.jsxs)(Hg, { children: [
			/* @__PURE__ */ (0, S.jsxs)("div", {
				className: "flex flex-wrap items-end gap-2",
				children: [/* @__PURE__ */ (0, S.jsx)("div", {
					className: "min-w-0 flex-1",
					children: /* @__PURE__ */ (0, S.jsx)(Zh, {
						"aria-label": "馆藏番号",
						isRequired: !0,
						isDisabled: l,
						value: t,
						onChange: n,
						placeholder: "输入馆藏番号，如 ABW-232"
					})
				}), /* @__PURE__ */ (0, S.jsx)(Hh, {
					type: "submit",
					disabled: !t.trim(),
					...$h(l || c.isPending),
					children: "抓取封面"
				})]
			}),
			l ? /* @__PURE__ */ (0, S.jsx)(hf, { label: "正在抓取封面" }) : null,
			d ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "error",
				children: d
			}) : null,
			a?.status === "complete" ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "success",
				children: a.result || "封面采集完成"
			}) : null
		] })
	});
}
function B_({ toast: e }) {
	let t = ct({
		queryKey: O_,
		queryFn: ({ signal: e }) => j_(e)
	}), n = t.data;
	return n ? /* @__PURE__ */ (0, S.jsxs)(_f, { children: [
		/* @__PURE__ */ (0, S.jsx)("p", {
			className: "text-body-2-regular text-text-secondary",
			children: "高清图片可能需要代理才能下载，请先检查连接。"
		}),
		/* @__PURE__ */ (0, S.jsx)(z_, { toast: e }),
		(n.sources || []).map((t) => /* @__PURE__ */ (0, S.jsx)(R_, {
			source: t,
			toast: e
		}, t.source))
	] }) : /* @__PURE__ */ (0, S.jsx)(_f, { children: /* @__PURE__ */ (0, S.jsx)(gf, {
		tone: "error",
		title: "读取失败",
		children: t.error ? ff(t.error) : "读取采集来源失败"
	}) });
}
//#endregion
//#region src/configuration-endpoints.ts
var V_ = "/api/configuration", H_ = "/api/pick-folder", U_ = ["configuration"], W_ = (e) => Q(V_, e);
async function G_(e) {
	await yf.fetchQuery({
		queryKey: U_,
		queryFn: () => W_(e)
	});
}
//#endregion
//#region src/react/boardui/components/base/switch/switch.tsx
var K_ = sf({
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
function q_({ state: e, size: t = "md", shape: n = "pill" }) {
	let r = K_[t];
	return /* @__PURE__ */ (0, S.jsx)("span", {
		"aria-hidden": !0,
		className: of("relative shrink-0 transition-colors duration-200 ease", r.track, r.trackRadius[n], e.isSelected ? of("bg-linear-to-b from-accent-500 to-accent-600", r.onShadow) : "bg-background-tertiary-default", e.isDisabled && "opacity-50", e.isFocusVisible && "ring-2 ring-border-focus-ring ring-offset-2"),
		children: /* @__PURE__ */ (0, S.jsx)("span", {
			className: of("absolute flex items-center justify-center", "bg-linear-to-b from-control-indicator-background from-[43.837%] to-control-indicator-background-subtle", "shadow-[0_3px_3px_0_rgb(0_0_0/0.03),0_0.75px_0_0_rgb(0_0_0/0.05)]", "transition-transform duration-200 ease", r.thumb, r.thumbRadius[n], r.offset, e.isSelected && r.travel),
			children: /* @__PURE__ */ (0, S.jsx)("span", { className: of("border-solid bg-linear-to-t from-[43.837%]", r.chip, r.chipRadius[n], e.isSelected ? "border-accent-600 from-switch-on-chip-start to-switch-on-chip-end" : "border-border-button-default/50 from-switch-off-chip-start to-switch-off-chip-end") })
		})
	});
}
function J_({ className: e, children: t, size: n = "md", shape: r = "pill", ref: i, ...a }) {
	return /* @__PURE__ */ (0, S.jsx)(Fh, {
		ref: i,
		...a,
		className: (t) => of("group inline-flex items-center gap-2 select-none", t.isDisabled ? "cursor-not-allowed" : "cursor-pointer", typeof e == "function" ? e(t) : e),
		children: (e) => /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)(q_, {
			state: e,
			size: n,
			shape: r
		}), t != null && t !== !1 && /* @__PURE__ */ (0, S.jsx)("span", {
			className: "text-body-medium text-text-primary",
			children: t
		})] })
	});
}
//#endregion
//#region src/react/settings/general-settings.tsx
function Y_({ data: e, receipt: t }) {
	return e.startup ? /* @__PURE__ */ (0, S.jsx)(X_, {
		startup: e.startup,
		receipt: t
	}) : null;
}
function X_({ startup: e, receipt: t }) {
	let [n, r] = (0, x.useState)(e.enabled), [i, a] = (0, x.useState)(e.silent), [o, s] = (0, x.useState)(e.desktop), c = Qh(), l = e.available && !e.desktop_message;
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "开机自启",
		onSubmit: (r) => {
			r.preventDefault(), e.available && c.run("save", (e) => pf("/api/configuration/startup", {
				enabled: n,
				silent: i,
				desktop: o
			}, "POST", e), () => t("已保存配置"));
		},
		children: [
			/* @__PURE__ */ (0, S.jsxs)(Vg, { children: [
				/* @__PURE__ */ (0, S.jsx)(zg, {
					label: "开机后启动 Peach",
					children: /* @__PURE__ */ (0, S.jsx)(J_, {
						"aria-label": "开机后启动 Peach",
						isSelected: n,
						isDisabled: !e.available,
						onChange: r
					})
				}),
				/* @__PURE__ */ (0, S.jsx)(zg, {
					label: "静默启动",
					description: "静默启动仅显示托盘，开机后启动 Peach 打开时生效。",
					children: /* @__PURE__ */ (0, S.jsx)(J_, {
						"aria-label": "静默启动",
						isSelected: i,
						isDisabled: !e.available || !n,
						onChange: a
					})
				}),
				/* @__PURE__ */ (0, S.jsx)(zg, {
					label: "在桌面创建快捷方式",
					description: e.desktop_message || "双击图标打开 Peach 网页；卸载时一并移除。",
					children: /* @__PURE__ */ (0, S.jsx)(J_, {
						"aria-label": "在桌面创建快捷方式",
						isSelected: o,
						isDisabled: !l,
						onChange: s
					})
				})
			] }),
			e.message || c.error ? /* @__PURE__ */ (0, S.jsxs)(Hg, {
				divided: !0,
				children: [e.message ? /* @__PURE__ */ (0, S.jsx)(Wg, { children: e.message }) : null, c.error ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: c.error }) : null]
			}) : null,
			/* @__PURE__ */ (0, S.jsx)(Ug, { children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				type: "submit",
				disabled: !e.available,
				...$h(c.busy === "save"),
				children: "保存配置"
			}) })
		]
	});
}
//#endregion
//#region src/react/boardui/components/base/checkbox/checkbox-glyph.tsx
var Z_ = {
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
function Q_({ state: e, size: t = "md" }) {
	let { isSelected: n, isIndeterminate: r, isFocusVisible: i, isDisabled: a, isHovered: o } = e, s = Z_[t], c = n || r, l = o && !a;
	return /* @__PURE__ */ (0, S.jsx)("span", {
		"aria-hidden": !0,
		className: of("flex shrink-0 items-center justify-center rounded-sm", "transition-[background-color,border-color,box-shadow] duration-150 ease", s.box, c ? of("bg-linear-to-b shadow-checkbox-selected", l ? "from-accent-400 to-accent-500" : "from-accent-500 to-accent-600") : of("border bg-background-primary-default shadow-xs", l ? "border-border-checkbox-hover" : "border-border-checkbox-default"), a && "opacity-50", i && "ring-2 ring-border-focus-ring ring-offset-2"),
		children: /* @__PURE__ */ (0, S.jsx)("svg", {
			viewBox: "0 0 16 16",
			fill: "none",
			className: s.glyph,
			children: r ? /* @__PURE__ */ (0, S.jsx)("path", {
				d: "M4.5 8H8H11.5",
				stroke: "white",
				strokeWidth: "2",
				strokeLinecap: "round"
			}) : n ? /* @__PURE__ */ (0, S.jsx)("path", {
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
function $_({ className: e, children: t, size: n = "md", ref: r, ...i }) {
	let a = Z_[n];
	return /* @__PURE__ */ (0, S.jsx)(xp, {
		ref: r,
		...i,
		className: (t) => of("group inline-flex items-center select-none", a.gap, t.isDisabled ? "cursor-not-allowed" : "cursor-pointer", typeof e == "function" ? e(t) : e),
		children: (e) => /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)(Q_, {
			state: e,
			size: n
		}), t != null && /* @__PURE__ */ (0, S.jsx)("span", {
			className: of(a.label, "text-text-primary"),
			children: t
		})] })
	});
}
//#endregion
//#region src/react/settings/media-repair.tsx
var ev = {
	status: "idle",
	stage: "",
	checked: 0,
	total: 0,
	found: 0,
	repaired: 0,
	failed: 0,
	skipped: 0,
	message: ""
}, tv = (e) => Number(e).toLocaleString();
function nv(e) {
	if (e.status === "running") {
		let t = e.total ? `${tv(e.checked)} / ${tv(e.total)}` : "准备中";
		return e.stage === "修复" && e.message ? `修复 ${t} · ${e.message}` : `${e.stage || "扫描"} ${t}`;
	}
	return e.status === "complete" && (e.repaired || e.failed) ? e.failed ? `修好 ${tv(e.repaired)} 部，${tv(e.failed)} 部修不了` : `修好 ${tv(e.repaired)} 部` : "";
}
function rv({ initial: e }) {
	let [t, n] = (0, x.useState)(e || ev), [r, i] = (0, x.useState)(!1), a = Qh(), o = t.status === "running";
	(0, x.useEffect)(() => {
		let e = new AbortController(), t, r = async () => {
			try {
				let i = await Q("/api/media-repair", e.signal);
				if (e.signal.aborted) return;
				n(i), i.status === "running" && (t = setTimeout(r, 2e3));
			} catch {}
		};
		return t = setTimeout(r, o ? 2e3 : 0), () => {
			e.abort(), clearTimeout(t);
		};
	}, [o]);
	let s = () => void a.run("start", (e) => pf("/api/media-repair", {
		allow_metered: r,
		restart: !0
	}, "POST", e), n), c = () => void a.run("stop", (e) => pf("/api/media-repair", { stop: !0 }, "POST", e), n), l = t.total ? Math.round(t.checked / t.total * 100) : 0;
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "播放兼容修复",
		children: [/* @__PURE__ */ (0, S.jsxs)(Hg, { children: [
			/* @__PURE__ */ (0, S.jsx)(Wg, { children: "有些 MP4 少了一张时间戳表，浏览器按容器给的时刻排帧，会把其中一部分丢掉，看着就是卡顿。 修好之后这类片子起播直接用原片，不再实时转码。原始文件不改动，修好的头另存在缓存里。" }),
			/* @__PURE__ */ (0, S.jsx)($_, {
				isSelected: r,
				isDisabled: o,
				onChange: i,
				children: "连 PikPak 上的一起修（要把片子完整拉一遍，走流量）"
			}),
			o ? /* @__PURE__ */ (0, S.jsx)(vf, {
				label: "修复进度",
				value: l
			}) : null,
			t.status === "complete" && !t.repaired && !t.failed ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "info",
				title: "没有要修的",
				children: "库里的片子都能直接播，没找到缺时间戳表的。"
			}) : null,
			a.error || t.error ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: a.error || t.error }) : null
		] }), /* @__PURE__ */ (0, S.jsx)(Ug, {
			status: nv(t) ? /* @__PURE__ */ (0, S.jsx)("p", {
				role: "status",
				children: nv(t)
			}) : null,
			children: o ? /* @__PURE__ */ (0, S.jsx)(Hh, {
				onClick: c,
				...$h(a.busy === "stop"),
				children: "停止"
			}) : /* @__PURE__ */ (0, S.jsx)(Hh, {
				onClick: s,
				...$h(a.busy === "start"),
				children: "开始修复"
			})
		})]
	});
}
//#endregion
//#region src/react/settings/release-updates.tsx
var iv = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]), av = [
	65,
	67,
	90
], ov = 120;
function sv({ initial: e, initialJob: t }) {
	let [n, r] = (0, x.useState)(e), [i, a] = (0, x.useState)(t || {
		state: "idle",
		progress: 0
	}), [s, c] = (0, x.useState)(""), l = Qh(), u = (0, x.useRef)(!1), d = (0, x.useRef)(!0), f = iv.has(i.state);
	(0, x.useEffect)(() => (d.current = !0, () => {
		d.current = !1;
	}), []);
	let p = async () => {
		let e = await pf("/api/configuration/update-restart", {});
		d.current && a(e);
	}, m = () => void o({
		title: "更新已准备好",
		body: `Peach ${i.version || ""} 将在重启后安装。`,
		confirmLabel: "立即重启",
		cancelLabel: "稍后",
		onConfirm: p
	});
	(0, x.useEffect)(() => {
		i.state !== "ready" || u.current || (u.current = !0, m());
	}, [i.state]), (0, x.useEffect)(() => {
		let e = new AbortController(), t = iv.has(i.state) ? 1e3 : 3e4, n, o = 0, s = async () => {
			try {
				let t = await Q("/api/configuration/update-status", e.signal);
				if (e.signal.aborted) return;
				a(t), o = 0, t.state === "complete" && r((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				}));
				let n = await Q("/api/configuration/automatic-updates", e.signal);
				!e.signal.aborted && n.result && r(n.result);
			} catch {
				o += 1, o >= ov && !e.signal.aborted && c("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && o < ov && (n = setTimeout(s, t));
		};
		return n = setTimeout(s, t), () => {
			e.abort(), clearTimeout(n);
		};
	}, [i.state]);
	let h = () => {
		f || (u.current = !1, c(""), l.run("download", (e) => pf("/api/configuration/update", {}, "POST", e), a));
	}, g = () => void l.run("check", (e) => Q("/api/configuration/updates", e), r, (t) => {
		r({
			...e,
			state: "error"
		}), l.setError(ff(t));
	}), _ = l.error || s, v = i.state === "downloading" && i.total ? `${((i.downloaded || 0) / 1048576).toFixed(1)} / ${(i.total / 1048576).toFixed(1)} MB` : `${i.progress}%`;
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "检查更新",
		children: [
			/* @__PURE__ */ (0, S.jsxs)(Jg, { children: [
				/* @__PURE__ */ (0, S.jsx)(Yg, {
					term: "当前版本",
					children: n.current_version
				}),
				/* @__PURE__ */ (0, S.jsx)(Yg, {
					term: "安装方式",
					children: n.installation
				}),
				/* @__PURE__ */ (0, S.jsx)(Yg, {
					term: "更新通道",
					children: n.channel
				}),
				/* @__PURE__ */ (0, S.jsx)(Yg, {
					term: "最新版本",
					children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得")
				})
			] }),
			/* @__PURE__ */ (0, S.jsxs)(Hg, {
				divided: !0,
				children: [
					n.checked_at ? /* @__PURE__ */ (0, S.jsxs)(Wg, { children: ["检查于 ", (/* @__PURE__ */ new Date(n.checked_at * 1e3)).toLocaleString()] }) : null,
					n.state === "available" && !_ ? /* @__PURE__ */ (0, S.jsx)(gf, {
						tone: "info",
						title: "有可用更新",
						children: n.message
					}) : _ || n.state === "error" ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: _ || n.message }) : /* @__PURE__ */ (0, S.jsx)(Wg, {
						role: "status",
						children: n.message
					}),
					i.state === "error" ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: i.message }) : null,
					i.state !== "idle" && i.state !== "error" ? /* @__PURE__ */ (0, S.jsxs)("div", {
						"aria-live": "polite",
						className: "flex flex-col gap-2",
						children: [
							/* @__PURE__ */ (0, S.jsx)(vf, {
								label: "更新准备进度：下载、校验、解压、准备安装",
								value: i.progress,
								stops: av
							}),
							/* @__PURE__ */ (0, S.jsxs)(Wg, { children: ["下载 → 校验 → 解压 → 准备安装 · ", i.message] }),
							/* @__PURE__ */ (0, S.jsx)(Wg, { children: v })
						]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, S.jsxs)(Ug, {
				status: /* @__PURE__ */ (0, S.jsx)(qg, {
					href: n.release_url,
					children: "查看发布页"
				}),
				children: [
					i.state === "ready" ? /* @__PURE__ */ (0, S.jsx)(Hh, {
						onClick: m,
						children: "重启安装"
					}) : null,
					n.state === "available" && n.installation === "独立测试包" && i.state !== "ready" ? /* @__PURE__ */ (0, S.jsx)(Hh, {
						onClick: h,
						...$h(f || l.busy === "download"),
						children: "下载并安装"
					}) : null,
					/* @__PURE__ */ (0, S.jsx)(Hh, {
						disabled: f,
						onClick: g,
						...$h(l.busy === "check"),
						children: "检查更新"
					})
				]
			})
		]
	});
}
//#endregion
//#region src/react/settings/maintenance-settings.tsx
var cv = [
	["6", "每 6 小时"],
	["24", "每天"],
	["168", "每周"]
];
function lv({ data: e, receipt: t }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex flex-col gap-6",
		children: [
			e.automatic_updates ? /* @__PURE__ */ (0, S.jsx)(uv, {
				initial: e.automatic_updates,
				receipt: t
			}) : null,
			e.updates ? /* @__PURE__ */ (0, S.jsx)(sv, {
				initial: e.updates,
				initialJob: e.update_job
			}) : null,
			/* @__PURE__ */ (0, S.jsx)(rv, {}),
			/* @__PURE__ */ (0, S.jsx)(dv, { facts: e.facts }),
			e.uninstall ? /* @__PURE__ */ (0, S.jsx)(fv, { uninstall: e.uninstall }) : null
		]
	});
}
function uv({ initial: e, receipt: t }) {
	let [n, r] = (0, x.useState)(e.mode), [i, a] = (0, x.useState)(e.interval_hours), o = Qh(e.error), s = (r) => {
		r.preventDefault(), e.available && o.run("save", (e) => pf("/api/configuration/automatic-updates", {
			mode: n,
			interval_hours: i
		}, "POST", e), () => t("已保存配置"));
	}, c = e.available ? e.download_available ? "开启后一分钟内开始检查。下载完成后，在此确认重启安装。" : "开启后一分钟内开始检查。源码运行请前往发布页获取新版本。" : "自动更新需要由托盘管理的服务。";
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "自动更新",
		onSubmit: s,
		children: [
			/* @__PURE__ */ (0, S.jsxs)(Vg, { children: [
				/* @__PURE__ */ (0, S.jsx)(zg, {
					label: "自动检查新版本",
					children: /* @__PURE__ */ (0, S.jsx)(J_, {
						"aria-label": "自动检查新版本",
						isSelected: n !== "off",
						isDisabled: !e.available,
						onChange: (e) => r(e ? "check" : "off")
					})
				}),
				/* @__PURE__ */ (0, S.jsx)(zg, {
					label: "自动下载更新",
					children: /* @__PURE__ */ (0, S.jsx)(J_, {
						"aria-label": "自动下载更新",
						isSelected: n === "download",
						isDisabled: !e.available || !e.download_available || n === "off",
						onChange: (e) => r(e ? "download" : "check")
					})
				}),
				/* @__PURE__ */ (0, S.jsx)(zg, {
					label: "检查频率",
					description: c,
					children: /* @__PURE__ */ (0, S.jsx)(S_, {
						"aria-label": "检查频率",
						selectedKey: String(i),
						isDisabled: !e.available,
						onSelectionChange: (e) => {
							e !== null && a(Number(e));
						},
						children: cv.map(([e, t]) => /* @__PURE__ */ (0, S.jsx)(C_, {
							id: e,
							children: t
						}, e))
					})
				})
			] }),
			o.error ? /* @__PURE__ */ (0, S.jsx)(Hg, {
				divided: !0,
				children: /* @__PURE__ */ (0, S.jsx)(Gg, { children: o.error })
			}) : null,
			/* @__PURE__ */ (0, S.jsx)(Ug, { children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				type: "submit",
				disabled: !e.available,
				...$h(o.busy === "save"),
				children: "保存配置"
			}) })
		]
	});
}
function dv({ facts: e }) {
	return /* @__PURE__ */ (0, S.jsx)(Bg, {
		title: "运行信息",
		children: /* @__PURE__ */ (0, S.jsx)(Jg, { children: e.map((e) => /* @__PURE__ */ (0, S.jsxs)(Yg, {
			term: e.term,
			children: [e.value, e.download_url ? /* @__PURE__ */ (0, S.jsx)(qg, {
				href: e.download_url,
				children: e.download_label
			}) : null]
		}, e.term)) })
	});
}
function fv({ uninstall: e }) {
	let [t, n] = (0, x.useState)(!1), [r, i] = (0, x.useState)(""), a = () => void o({
		title: "卸载 Peach",
		danger: !0,
		body: t ? "将退出 Peach，移除程序、开机自启、桌面图标、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序、开机自启和桌面图标。设置、本地数据库、观看记录与缓存保留。",
		confirmLabel: "卸载 Peach",
		onConfirm: async () => {
			let e = await pf("/api/configuration/uninstall", {
				delete_data: t,
				confirmation: "卸载 Peach"
			});
			i(e.message);
		}
	}), s = r || e.message, c = [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])];
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		id: "uninstallPeach",
		title: "卸载 Peach",
		children: [/* @__PURE__ */ (0, S.jsxs)(Hg, { children: [
			e.available ? /* @__PURE__ */ (0, S.jsx)(Wg, { children: "卸载会退出 Peach、移除程序、开机自启和桌面图标。原始媒体文件保留。" }) : null,
			/* @__PURE__ */ (0, S.jsx)($_, {
				isSelected: t,
				isDisabled: !e.full_available || !!r,
				onChange: n,
				children: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存"
			}),
			/* @__PURE__ */ (0, S.jsx)(Xg, {
				summary: "数据目录",
				children: c.map((e) => /* @__PURE__ */ (0, S.jsx)("p", {
					className: "text-body-2-regular break-all text-text-secondary",
					children: e
				}, e))
			})
		] }), /* @__PURE__ */ (0, S.jsx)(Ug, {
			status: s ? /* @__PURE__ */ (0, S.jsx)("p", {
				role: r ? "status" : void 0,
				children: s
			}) : null,
			children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				variant: "danger",
				disabled: !e.available || !!r,
				onClick: a,
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/react/settings/clouddrive-guide.tsx
var pv = [
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
], mv = [
	["cache", "缓存上限"],
	["read", "读取长度（默认 / 最小）"],
	["task", "同时处理视频"]
];
function hv() {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "@container flex flex-col gap-3",
		children: [/* @__PURE__ */ (0, S.jsxs)(Wg, { children: ["先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。", /* @__PURE__ */ (0, S.jsx)(qg, {
			href: "https://www.clouddrive2.com/help.html",
			children: "挂载帮助"
		})] }), /* @__PURE__ */ (0, S.jsxs)(Xg, {
			summary: "CloudDrive 缓存建议",
			children: [
				/* @__PURE__ */ (0, S.jsx)(Wg, { children: "看缓存放在哪块硬盘上，照那一档填。这是起步值，填得越大不一定越快。" }),
				/* @__PURE__ */ (0, S.jsx)("ul", {
					"aria-label": "按缓存所在硬盘分档",
					className: "flex flex-col gap-2",
					children: pv.map((e) => /* @__PURE__ */ (0, S.jsxs)("li", {
						className: "flex flex-col gap-2 rounded-2lg border border-separator-border bg-background-primary-default p-3",
						children: [/* @__PURE__ */ (0, S.jsx)("p", {
							className: "text-body-medium text-text-primary",
							children: e.name
						}), /* @__PURE__ */ (0, S.jsx)("dl", {
							className: "inline-grid grid-cols-1 gap-2 @md:grid-cols-3",
							children: mv.map(([t, n]) => /* @__PURE__ */ (0, S.jsxs)("div", {
								className: "flex flex-col",
								children: [/* @__PURE__ */ (0, S.jsx)("dt", {
									className: "text-caption-1-regular text-text-secondary",
									children: n
								}), /* @__PURE__ */ (0, S.jsx)("dd", {
									className: "text-body-regular text-text-primary",
									children: e[t]
								})]
							}, t))
						})]
					}, e.name))
				}),
				/* @__PURE__ */ (0, S.jsxs)("ul", {
					className: "flex list-disc flex-col gap-1 pl-5 text-body-2-regular text-text-secondary",
					children: [
						/* @__PURE__ */ (0, S.jsx)("li", { children: "缓存上限和清理方式填在 CloudDrive「设置」里，清理方式选 LRU。上限不要填 0，系统盘至少留 40 GiB；填完重开设置页确认存住了。" }),
						/* @__PURE__ */ (0, S.jsx)("li", { children: "读取长度和下载线程填在每个网盘各自的下载设置里，线程都从 2 开始。" }),
						/* @__PURE__ */ (0, S.jsx)("li", { children: "Buffer Cache 占内存，磁盘缓存和文件夹缓存占硬盘，改一个管不住另外两个。" })
					]
				}),
				/* @__PURE__ */ (0, S.jsxs)(Wg, { children: [
					"三处缓存分别管什么、这几个值怎么往上调、码率和速度怎么换算、线程上限与直链代理怎么取舍，以及这些起步值的来源，都在",
					/* @__PURE__ */ (0, S.jsx)(qg, {
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
var gv = [
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
function _v(e) {
	let t = e === "local" ? "" : a[e];
	return t ? [t, "自动识别"] : ["hard-drive", "默认"];
}
var vv = "auto";
function yv({ value: e, label: t, kind: n = "local", onChange: r }) {
	let i = (0, x.useRef)(null), [a, o] = (0, x.useState)(!1), [s, c] = (0, x.useState)(e), [l, u] = _v(n);
	return /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)(Hh, {
		ref: i,
		variant: "secondary",
		className: "self-start",
		"aria-label": t,
		"aria-haspopup": "dialog",
		"aria-expanded": a,
		onClick: () => {
			c(e), o(!0);
		},
		children: /* @__PURE__ */ (0, S.jsxs)("span", {
			"data-icon-choice": !0,
			className: "flex items-center gap-2",
			children: [/* @__PURE__ */ (0, S.jsx)(Qg, { mark: e || l }), ((e) => e && gv.find(([t]) => t === e)?.[1] || u)(e)]
		})
	}), /* @__PURE__ */ (0, S.jsx)(Qm, {
		triggerRef: i,
		isOpen: a,
		onOpenChange: o,
		placement: "bottom start",
		offset: 4,
		className: Mg,
		children: /* @__PURE__ */ (0, S.jsxs)(nh, {
			"aria-label": `${t}候选`,
			className: "flex w-72 flex-col gap-3 outline-none",
			children: [
				/* @__PURE__ */ (0, S.jsx)(fp, {
					slot: "title",
					className: "px-1 text-body-medium text-text-primary",
					children: "选择媒体库图标"
				}),
				/* @__PURE__ */ (0, S.jsx)(yh, {
					"aria-label": "候选图标",
					value: s || vv,
					onChange: (e) => c(e === vv ? "" : e),
					className: "inline-grid grid-cols-7 gap-1",
					children: gv.map(([e, t]) => /* @__PURE__ */ (0, S.jsx)(bh, {
						value: e || vv,
						"aria-label": e ? t : u,
						className: "flex h-10 cursor-pointer items-center justify-center rounded-lg text-foreground-icon-secondary outline-none hover:bg-dropdown-item-hover-background focus-visible:ring-2 focus-visible:ring-border-focus-ring data-selected:bg-dropdown-item-hover-background data-selected:text-text-primary",
						children: /* @__PURE__ */ (0, S.jsx)(Qg, { mark: e || l })
					}, e || vv))
				}),
				/* @__PURE__ */ (0, S.jsxs)("div", {
					className: "flex justify-end gap-2 border-t border-separator-border pt-2.5",
					children: [/* @__PURE__ */ (0, S.jsx)(Hh, {
						variant: "secondary",
						onClick: () => o(!1),
						children: "取消"
					}), /* @__PURE__ */ (0, S.jsx)(Hh, {
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
var bv = 8e3;
function xv({ className: e }) {
	return /* @__PURE__ */ (0, S.jsx)("svg", {
		"aria-hidden": !0,
		viewBox: "0 0 24 24",
		fill: "none",
		stroke: "currentColor",
		strokeWidth: 2,
		strokeLinecap: "round",
		strokeLinejoin: "round",
		className: e,
		children: /* @__PURE__ */ (0, S.jsx)("use", { href: "#i-folder-search" })
	});
}
var Sv = [
	["local", "本地磁盘"],
	["115", "CloudDrive · 115"],
	["pikpak", "CloudDrive · PikPak"]
], Cv = (e) => Sv.find(([t]) => t === e)?.[1] ?? e, wv = (e) => a[e] || "database", Tv = (e = "") => ({
	path: e,
	location: "local",
	root: "",
	library: "",
	library_icon: ""
});
function Ev(e) {
	let t = e.media_sources?.filter((e) => Sv.some(([t]) => t === e.location));
	return t?.length ? t.map((e) => ({
		path: e.path,
		location: e.location,
		root: e.root,
		library: e.library || "",
		library_icon: e.library_icon || ""
	})) : (e.media_dirs.length ? e.media_dirs : [""]).map((e) => Tv(e));
}
var Dv = (e) => !(e instanceof uf) || e.status !== 400 ? null : e.body?.errors ?? null;
function Ov({ data: e, receipt: t }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex flex-col gap-6",
		children: [e.editable ? /* @__PURE__ */ (0, S.jsx)(kv, {
			data: e,
			receipt: t
		}) : /* @__PURE__ */ (0, S.jsx)(gf, {
			tone: "neutral",
			title: "只读",
			children: e.notice
		}), /* @__PURE__ */ (0, S.jsx)(jv, { data: e })]
	});
}
function kv({ data: e, receipt: t }) {
	let [n, r] = (0, x.useState)(() => Ev(e)), [i, a] = (0, x.useState)(String(e.port)), [o, s] = (0, x.useState)(!1), [c, l] = (0, x.useState)([]), [u, d] = (0, x.useState)(""), [f, p] = (0, x.useState)(""), [m, h] = (0, x.useState)(null), [g, _] = (0, x.useState)(null), [v, y] = (0, x.useState)(null), b = (0, x.useRef)(!1), C = (0, x.useRef)(e.revision), w = (0, x.useRef)([]), T = Qh();
	(0, x.useLayoutEffect)(() => {
		g !== null && (w.current[g]?.focus(), _(null));
	}, [g]), (0, x.useEffect)(() => {
		if (!m) return;
		let e = setTimeout(() => location.assign(m.url), bv);
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
		_(n.length), r((e) => [...e, Tv()]);
	}, k = (e) => {
		r((t) => t.filter((t, n) => n !== e)), l((t) => t.filter((t, n) => n !== e));
	}, A = async (e) => {
		if (!b.current) {
			b.current = !0, y(e);
			try {
				let { path: t } = await pf(H_, { initial: n[e]?.path ?? "" });
				t && (E(e, { path: t }), D(e, ""));
			} catch (t) {
				D(e, ff(t));
			} finally {
				b.current = !1, y(null);
			}
		}
	}, ee = (r) => {
		r.preventDefault(), p(""), T.run("save", (t) => pf(V_, {
			revision: C.current,
			media_dirs: n.map((e) => e.path),
			...e.media_sources ? { media_sources: n } : {},
			port: i,
			scan_now: o
		}, "POST", t), (e) => {
			C.current = e.revision, l([]), d(""), t("已保存配置"), h(e);
		}, (e) => {
			let t = Dv(e);
			l(t?.media_dirs ?? []), d(t?.port ?? ""), t || p(ff(e));
		});
	};
	if (m) return /* @__PURE__ */ (0, S.jsx)(Bg, {
		title: "这台电脑",
		children: /* @__PURE__ */ (0, S.jsx)(Hg, { children: /* @__PURE__ */ (0, S.jsxs)(gf, {
			tone: "success",
			title: "配置已保存",
			children: [
				"Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ (0, S.jsx)(jg, {
					href: m.url,
					size: "small",
					children: "进入馆藏"
				}),
				"。"
			]
		}) })
	});
	let j = n.some((e) => e.location === "115" || e.location === "pikpak"), te = j ? (e.mount_dependencies ?? []).filter((e) => !e.available) : [];
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "这台电脑",
		onSubmit: ee,
		children: [/* @__PURE__ */ (0, S.jsxs)(Hg, { children: [
			/* @__PURE__ */ (0, S.jsxs)("div", {
				className: "flex flex-col gap-3",
				children: [
					/* @__PURE__ */ (0, S.jsx)(Kg, { children: "媒体文件夹" }),
					/* @__PURE__ */ (0, S.jsx)("div", {
						role: "group",
						"aria-label": "媒体文件夹",
						className: "flex flex-col gap-3",
						children: n.map((t, r) => /* @__PURE__ */ (0, S.jsxs)("div", {
							"data-folder-row": !0,
							className: "@container flex flex-col gap-3 rounded-2lg border border-separator-border bg-background-primary-default p-3",
							children: [/* @__PURE__ */ (0, S.jsxs)("div", {
								className: "flex items-start gap-2",
								children: [
									/* @__PURE__ */ (0, S.jsx)(Zh, {
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
									/* @__PURE__ */ (0, S.jsx)(Wh, {
										icon: xv,
										"aria-label": "选择文件夹",
										onClick: () => void A(r),
										...$h(v === r)
									}),
									n.length > 1 ? /* @__PURE__ */ (0, S.jsx)(Wh, {
										icon: _u,
										"aria-label": "移除这个文件夹",
										onClick: () => k(r)
									}) : null
								]
							}), /* @__PURE__ */ (0, S.jsxs)("div", {
								className: "inline-grid grid-cols-1 gap-3 @lg:grid-cols-2",
								children: [
									/* @__PURE__ */ (0, S.jsx)(Zh, {
										label: "媒体库名称",
										maxLength: 80,
										placeholder: "同名文件夹归入同一个媒体库",
										value: t.library,
										onChange: (e) => E(r, { library: e })
									}),
									/* @__PURE__ */ (0, S.jsxs)("div", {
										className: "flex flex-col gap-1.5",
										children: [/* @__PURE__ */ (0, S.jsx)(Kg, { children: "媒体库图标" }), /* @__PURE__ */ (0, S.jsx)(yv, {
											label: `媒体库图标 ${r + 1}`,
											value: t.library_icon,
											kind: t.location,
											onChange: (e) => E(r, { library_icon: e })
										})]
									}),
									/* @__PURE__ */ (0, S.jsxs)("div", {
										className: "flex flex-col gap-1.5",
										children: [/* @__PURE__ */ (0, S.jsx)(Kg, { children: "媒体来源" }), /* @__PURE__ */ (0, S.jsx)(S_, {
											"aria-label": `媒体来源 ${r + 1}`,
											selectedKey: t.location,
											onSelectionChange: (e) => {
												e !== null && E(r, { location: String(e) });
											},
											children: Sv.map(([e, t]) => /* @__PURE__ */ (0, S.jsxs)(C_, {
												id: e,
												textValue: t,
												children: [/* @__PURE__ */ (0, S.jsx)(Qg, { mark: wv(e) }), t]
											}, e))
										})]
									}),
									e.windows === !1 ? /* @__PURE__ */ (0, S.jsx)(Zh, {
										label: "Windows 中的对应路径",
										placeholder: "例如 B:\\",
										value: t.root,
										onChange: (e) => E(r, { root: e })
									}) : null
								]
							})]
						}, r))
					}),
					/* @__PURE__ */ (0, S.jsx)(Hh, {
						className: "self-start",
						onClick: O,
						children: "添加文件夹"
					})
				]
			}),
			j ? /* @__PURE__ */ (0, S.jsx)(hv, {}) : null,
			te.map((e) => /* @__PURE__ */ (0, S.jsxs)(Wg, { children: [
				"未检测到 ",
				e.name,
				"。",
				/* @__PURE__ */ (0, S.jsxs)(qg, {
					href: e.download_url,
					children: ["下载 ", e.name]
				})
			] }, e.name)),
			e.windows === !1 ? /* @__PURE__ */ (0, S.jsx)(Wg, { children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。" }) : null,
			e.port_editable === !1 ? null : /* @__PURE__ */ (0, S.jsx)(Zh, {
				id: "configPort",
				label: "本机访问端口",
				inputMode: "numeric",
				value: i,
				onChange: a,
				validationBehavior: "aria",
				isInvalid: !!u,
				hint: u || "浏览器地址里冒号后面的数字，一般不用改。"
			}),
			/* @__PURE__ */ (0, S.jsx)($_, {
				isSelected: o,
				onChange: s,
				children: "保存后扫描并补全资料"
			}),
			f ? /* @__PURE__ */ (0, S.jsx)(gf, {
				tone: "error",
				title: "没有保存",
				children: f
			}) : null
		] }), /* @__PURE__ */ (0, S.jsx)(Ug, {
			status: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。",
			children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				type: "submit",
				...$h(T.busy === "save"),
				children: "保存配置"
			})
		})]
	});
}
function Av({ online: e }) {
	return e === !0 ? /* @__PURE__ */ (0, S.jsxs)("span", {
		"data-mount": "online",
		className: "inline-flex items-center gap-1.5 text-body-2-medium text-notification-success-foreground",
		children: [/* @__PURE__ */ (0, S.jsx)("span", {
			"aria-hidden": !0,
			className: "size-1.5 rounded-full bg-current"
		}), "在线"]
	}) : e === !1 ? /* @__PURE__ */ (0, S.jsxs)("span", {
		"data-mount": "offline",
		className: "inline-flex items-center gap-1.5 text-body-2-medium text-text-error-primary",
		children: [/* @__PURE__ */ (0, S.jsx)("span", {
			"aria-hidden": !0,
			className: "size-1.5 rounded-full bg-current"
		}), "离线"]
	}) : /* @__PURE__ */ (0, S.jsxs)("span", {
		"data-mount": "unknown",
		className: "inline-flex items-center gap-1.5 text-body-2-medium text-text-secondary",
		children: [/* @__PURE__ */ (0, S.jsx)("span", {
			"aria-hidden": !0,
			className: "size-1.5 rounded-full bg-current"
		}), "未检测"]
	});
}
function jv({ data: e }) {
	let t = e.media_sources, n = Qh();
	return t ? /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "挂载状态",
		children: [
			/* @__PURE__ */ (0, S.jsx)(Jg, { children: t.map((e, t) => /* @__PURE__ */ (0, S.jsxs)(Yg, {
				term: /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)(Qg, { mark: wv(e.location) }), Cv(e.location)] }),
				children: [e.path || "未配置挂载点", /* @__PURE__ */ (0, S.jsx)(Av, { online: e.online })]
			}, t)) }),
			n.error ? /* @__PURE__ */ (0, S.jsx)(Hg, {
				divided: !0,
				children: /* @__PURE__ */ (0, S.jsx)(Gg, { children: n.error })
			}) : null,
			/* @__PURE__ */ (0, S.jsx)(Ug, { children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				onClick: () => void n.run("refresh", (e) => W_(e), (e) => yf.setQueryData(U_, e)),
				...$h(n.busy === "refresh"),
				children: "刷新挂载状态"
			}) })
		]
	}) : null;
}
//#endregion
//#region src/react/settings/access-settings.tsx
var Mv = {
	legacy: "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。",
	locked: "访问设置无法读取，请在本机检查配置文件。",
	password: "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
};
function Nv({ initial: e, receipt: t }) {
	let [n, r] = (0, x.useState)(e), [i, a] = (0, x.useState)(""), [o, s] = (0, x.useState)(""), [c, l] = (0, x.useState)(""), [u, d] = (0, x.useState)(!1), [f, p] = (0, x.useState)({}), m = (0, x.useRef)(null), h = Qh(), g = (e) => {
		e.preventDefault();
		let f = {};
		if (n.mode === "password" && !i && (f.current_password = "请输入当前访问密码"), u || ((o.length < 8 || o.length > 256) && (f.password = "访问密码需为 8–256 个字符"), o !== c && (f.confirmation = "两次输入的密码不一致")), p(f), Object.keys(f).length) {
			requestAnimationFrame(() => m.current?.querySelector("input[aria-invalid=\"true\"]")?.focus());
			return;
		}
		h.run("save", (e) => pf("/api/configuration/access", {
			revision: n.revision,
			action: u ? "disable" : "set",
			confirm_disable: u,
			current_password: i,
			password: u ? "" : o,
			confirmation: u ? "" : c
		}, "POST", e), (e) => {
			r(e), a(""), s(""), l(""), d(!1), p({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存配置");
		}, (e) => {
			let t = e instanceof uf ? e.body : null, n = t?.errors || t?.detail?.errors;
			n ? p(n) : h.setError(ff(e));
		});
	}, _ = Mv[n.mode], v = n.mode !== "locked";
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		title: "访问密码",
		onSubmit: g,
		children: [/* @__PURE__ */ (0, S.jsx)("div", {
			ref: m,
			children: /* @__PURE__ */ (0, S.jsxs)(Hg, { children: [
				_ ? /* @__PURE__ */ (0, S.jsx)(Wg, { children: _ }) : null,
				n.mode === "open" ? /* @__PURE__ */ (0, S.jsx)(gf, {
					tone: "warning",
					title: "未设置访问密码",
					children: "能连接到 Peach 的设备打开地址就能看馆藏，不需要登录。"
				}) : null,
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ (0, S.jsx)($_, {
					isSelected: u,
					onChange: d,
					children: "关闭访问密码，允许能连接到 Peach 的设备直接访问"
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ (0, S.jsx)(Zh, {
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
				v ? /* @__PURE__ */ (0, S.jsxs)(S.Fragment, { children: [/* @__PURE__ */ (0, S.jsx)(Zh, {
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
				}), /* @__PURE__ */ (0, S.jsx)(Zh, {
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
				u ? /* @__PURE__ */ (0, S.jsx)(gf, {
					tone: "warning",
					title: "访问范围",
					children: "保存后，能连接到 Peach 的设备将直接访问馆藏。"
				}) : null,
				h.error ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: h.error }) : null
			] })
		}), v ? /* @__PURE__ */ (0, S.jsx)(Ug, {
			status: "保存后立即生效。",
			children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				type: "submit",
				...$h(h.busy === "save"),
				children: "保存配置"
			})
		}) : null]
	});
}
//#endregion
//#region src/react/settings/network-settings.tsx
var Pv = [
	["environment", "系统代理"],
	["direct", "直连"],
	["proxy", "自定义"]
];
function Fv({ data: e, receipt: t }) {
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "flex flex-col gap-6",
		children: [e.peach_proxy ? /* @__PURE__ */ (0, S.jsx)(Iv, {
			initial: e.peach_proxy,
			receipt: t
		}) : null, e.access ? /* @__PURE__ */ (0, S.jsx)(Nv, {
			initial: e.access,
			receipt: t
		}) : null]
	});
}
function Iv({ initial: e, receipt: t }) {
	let [n, r] = (0, x.useState)(e), [i, a] = (0, x.useState)(e.mode), [o, s] = (0, x.useState)(""), c = Qh();
	return /* @__PURE__ */ (0, S.jsxs)(Bg, {
		id: "peachProxy",
		title: "Peach 代理",
		onSubmit: (e) => {
			e.preventDefault(), c.run("save", (e) => pf("/api/configuration/peach-proxy", {
				mode: i,
				proxy: o
			}, "POST", e), (e) => {
				r(e), s(""), t("已保存配置");
			});
		},
		children: [
			/* @__PURE__ */ (0, S.jsx)(Vg, { children: /* @__PURE__ */ (0, S.jsx)(zg, {
				label: "连接方式",
				description: "采集来源选择“Peach 代理”时共用此设置。",
				children: /* @__PURE__ */ (0, S.jsx)(S_, {
					"aria-label": "连接方式",
					selectedKey: i,
					onSelectionChange: (e) => {
						e !== null && a(String(e));
					},
					children: Pv.map(([e, t]) => /* @__PURE__ */ (0, S.jsx)(C_, {
						id: e,
						children: t
					}, e))
				})
			}) }),
			i === "proxy" || n.needs_selection || c.error ? /* @__PURE__ */ (0, S.jsxs)(Hg, {
				divided: !0,
				children: [
					i === "proxy" ? /* @__PURE__ */ (0, S.jsx)(Zh, {
						id: "peachProxyAddress",
						type: "password",
						label: "代理地址",
						autoComplete: "off",
						value: o,
						onChange: s,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890"
					}) : null,
					n.needs_selection ? /* @__PURE__ */ (0, S.jsx)(gf, {
						tone: "warning",
						title: "需要选择连接方式",
						children: "已有来源的代理地址不同，请选择公共连接方式。"
					}) : null,
					c.error ? /* @__PURE__ */ (0, S.jsx)(Gg, { children: c.error }) : null
				]
			}) : null,
			/* @__PURE__ */ (0, S.jsx)(Ug, { children: /* @__PURE__ */ (0, S.jsx)(Hh, {
				type: "submit",
				...$h(c.busy === "save"),
				children: "保存配置"
			}) })
		]
	});
}
//#endregion
//#region src/react/settings/configuration-page.tsx
function Lv({ receipt: e }) {
	let t = ct({
		queryKey: U_,
		queryFn: ({ signal: e }) => W_(e)
	}), n = t.data;
	if (!n) return /* @__PURE__ */ (0, S.jsx)("div", {
		className: "configpage",
		children: /* @__PURE__ */ (0, S.jsx)(gf, {
			tone: "error",
			title: "打不开配置",
			children: t.error ? ff(t.error) : "没有读到配置"
		})
	});
	let r = {
		data: n,
		receipt: e
	}, i = !!(n.peach_proxy || n.access);
	return /* @__PURE__ */ (0, S.jsxs)("div", {
		className: "configpage",
		children: [
			n.startup ? /* @__PURE__ */ (0, S.jsx)("h2", {
				className: "configgroup",
				children: "通用"
			}) : null,
			n.startup ? /* @__PURE__ */ (0, S.jsx)(Y_, { ...r }) : null,
			/* @__PURE__ */ (0, S.jsx)("h2", {
				className: "configgroup",
				children: "媒体"
			}),
			/* @__PURE__ */ (0, S.jsx)(Ov, { ...r }),
			i ? /* @__PURE__ */ (0, S.jsx)("h2", {
				className: "configgroup",
				children: "网络与访问"
			}) : null,
			i ? /* @__PURE__ */ (0, S.jsx)(Fv, { ...r }) : null,
			/* @__PURE__ */ (0, S.jsx)("h2", {
				className: "configgroup",
				children: "更新与维护"
			}),
			/* @__PURE__ */ (0, S.jsx)(lv, { ...r })
		]
	});
}
//#endregion
//#region src/react/entry.tsx
var Rv = null;
function zv() {
	return Rv?.isConnected || (Rv = document.createElement("div"), Rv.className = "peach-react", Rv.dataset.reactOverlays = "", document.body.append(Rv)), Rv;
}
function Bv(e) {
	return (t, n) => {
		let r = (0, fu.createRoot)(t), i = (t) => r.render(/* @__PURE__ */ (0, S.jsx)(T, {
			client: yf,
			children: /* @__PURE__ */ (0, S.jsx)(lc, {
				getContainer: zv,
				children: /* @__PURE__ */ (0, S.jsx)(e, { ...t })
			})
		}));
		return (0, Kr.flushSync)(() => i(n)), {
			update: i,
			unmount: () => r.unmount()
		};
	};
}
var Vv = {
	activity: {
		prefetch: (e, t) => Ef(t),
		mount: Bv($)
	},
	"avatar-picker": {
		prefetch: async () => {},
		mount: Bv(fg)
	},
	configuration: {
		prefetch: (e, t) => G_(t),
		mount: Bv(Lv)
	},
	"library-processing": {
		prefetch: (e, t) => _g(t),
		mount: Bv((e) => e.mode === "notice" ? /* @__PURE__ */ (0, S.jsx)(u_, { ...e }) : /* @__PURE__ */ (0, S.jsx)(s_, { ...e }))
	},
	"quality-goals": {
		prefetch: (e, t) => m_(t),
		mount: Bv(__)
	},
	scraping: {
		prefetch: (e, t) => N_(t),
		mount: Bv(B_)
	}
};
//#endregion
export { Vv as pages };
