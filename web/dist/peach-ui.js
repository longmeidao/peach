import { MEDIA_SOURCE_ICONS as e, checkboxHtml as t, confirmModal as n, emptyStateHtml as r, fieldsetTitle as i, loadingDotsHtml as a, noteHtml as o, progressHtml as s, selectFieldHtml as c, selectOptionIconHtml as l, setActionBusy as u, wireCollapse as d, wireSelectField as f } from "/js/ui-components.js";
import { LOC as p, esc as m, faviconUrl as h, fmtDur as g, fmtSize as _, icon as v } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var y, b, x, S, C, w, T, E, D, O, k, A, ee, j, M, N = {}, P = [], te = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, ne = Array.isArray;
function F(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function re(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function ie(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? y.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return ae(e, o, r, i, null);
}
function ae(e, t, n, r, i) {
	var a = {
		type: e,
		props: t,
		key: n,
		ref: r,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: i ?? ++x,
		__i: -1,
		__u: 0
	};
	return i == null && b.vnode != null && b.vnode(a), a;
}
function I(e) {
	return e.children;
}
function oe(e, t) {
	this.props = e, this.context = t;
}
function L(e, t) {
	if (t == null) return e.__ ? L(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? L(e) : null;
}
function se(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = F({}, t);
		a.__v = t.__v + 1, b.vnode && b.vnode(a), ve(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? L(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, be(r, a, i), t.__e = t.__ = null, a.__e != n && ce(a);
	}
}
function ce(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), ce(e);
}
function le(e) {
	(!e.__d && (e.__d = !0) && C.push(e) && !ue.__r++ || w != b.debounceRendering) && ((w = b.debounceRendering) || T)(ue);
}
function ue() {
	try {
		for (var e, t = 1; C.length;) C.length > t && C.sort(E), e = C.shift(), t = C.length, se(e);
	} finally {
		C.length = ue.__r = 0;
	}
}
function de(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || P, v = t.length;
	for (c = fe(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || N, p.__i = d, g = ve(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && Ce(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = pe(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function fe(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = ae(null, o, null, null, null) : ne(o) ? o = e.__k[a] = ae(I, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = ae(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = me(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = L(s)), we(s, s));
	return r;
}
function pe(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = pe(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = L(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function me(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function he(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || te.test(t) ? n : n + "px";
}
function ge(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || he(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || he(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(A, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[k] = r[k] : (n[k] = ee, e.addEventListener(t, a ? M : j, a)) : e.removeEventListener(t, a ? M : j, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function _e(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[O] == null) t[O] = ee++;
			else if (t[O] < n[k]) return;
			return n(b.event ? b.event(t) : t);
		}
	};
}
function ve(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, y, x, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = b.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, y = D.prototype && D.prototype.render, x = (u = D.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (y ? t.__c = f = new D(v, S) : (t.__c = f = new oe(v, S), f.constructor = D, f.render = Te), x && x.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), y && f.__s == null && (f.__s = f.state), y && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = F({}, f.__s)), F(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) y && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), y && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (y && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, S)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), P.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = L(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, S), y && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = S, f.props = v, f.__P = e, f.__e = !1, C = b.__r, w = 0, y) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), P.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = F(F({}, r), f.getChildContext())), y && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === I && u.key == null ? xe(u.props.children) : u, s = de(e, ne(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) re(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || ye(t), b.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = Se(n.__e, t, n, r, i, a, o, c, l);
	return (u = b.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function ye(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(ye));
}
function be(e, t, n) {
	for (var r = 0; r < n.length; r++) Ce(n[r], n[++r], n[++r]);
	b.__c && b.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			b.__e(e, t.__v);
		}
	});
}
function xe(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : ne(e) ? e.map(xe) : e.constructor === void 0 ? F({}, e) : null;
}
function Se(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || N, _ = t.props, v = t.type;
	if (v == "svg" ? i = "http://www.w3.org/2000/svg" : v == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!v && (v ? p.localName == v : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (v == null) return document.createTextNode(_);
		e = document.createElementNS(i, v, _.is && _), s &&= (b.__m && b.__m(t, a), !1), a = null;
	}
	if (v == null) g === _ || s && e.data == _ || (e.data = _);
	else {
		if (a = v == "textarea" && _.defaultValue != null ? null : a && y.call(e.childNodes), !s && a != null) for (g = {}, l = 0; l < e.attributes.length; l++) g[(p = e.attributes[l]).name] = p.value;
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || ge(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || ge(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), de(t.type == "template" ? e.content : e, ne(f) ? f : [f], t, n, r, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && L(n, 0), s, c), a != null) for (l = a.length; l--;) re(a[l]);
		s && v != "textarea" || (l = "value", v == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || v == "progress" && !m || v == "option" && m != g[l]) && ge(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && ge(e, l, h, g[l], i));
	}
	return e;
}
function Ce(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		b.__e(e, n);
	}
}
function we(e, t, n) {
	var r, i;
	if (b.unmount && b.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || Ce(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			b.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && we(r[i], t, n || typeof e.type != "function");
	n || re(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Te(e, t, n) {
	return this.constructor(e, n);
}
function Ee(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), b.__ && b.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], ve(t, e = (!r && n || t).__k = ie(I, null, [e]), i || N, N, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? y.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), be(a, e, o), e.props.children = null;
}
y = P.slice, b = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, x = 0, S = function(e) {
	return e != null && e.constructor === void 0;
}, oe.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = F({}, this.state);
	typeof e == "function" && (e = e(F({}, n), this.props)), e && F(n, e), e != null && this.__v && (t && this._sb.push(t), le(this));
}, oe.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), le(this));
}, oe.prototype.render = I, C = [], T = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, E = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, ue.__r = 0, D = Math.random().toString(8), O = "__d" + D, k = "__a" + D, A = /(PointerCapture)$|Capture$/i, ee = 0, j = _e(!1), M = _e(!0);
//#endregion
//#region src/sort-preferences.ts
function De(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/api.ts
var Oe = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, ke = (e) => {
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
}, R = (e) => e instanceof Error ? e.message : String(e);
async function z(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Oe(ke(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function B(e, t, n = "POST", r) {
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
	if (!i.ok) throw new Oe(ke(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var V, H, Ae, je, Me = 0, Ne = [], U = b, Pe = U.__b, Fe = U.__r, Ie = U.diffed, Le = U.__c, Re = U.unmount, ze = U.__;
function Be(e, t) {
	U.__h && U.__h(H, e, Me || t), Me = 0;
	var n = H.__H || (H.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function W(e) {
	return Me = 1, Ve(Ye, e);
}
function Ve(e, t, n) {
	var r = Be(V++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Ye(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = H, !H.__f)) {
		var i = function(e, t, n) {
			if (!r.__c.__H) return !0;
			var i = !1, o = r.__c.props !== e;
			if (r.__c.__H.__.some(function(e) {
				if (e.__N) {
					i = !0;
					var t = e.__[0];
					e.__ = e.__N, e.__N = void 0, t !== e.__[0] && (o = !0);
				}
			}), a) {
				var s = a.call(this, e, t, n);
				return i ? s || o : s;
			}
			return !i || o;
		};
		H.__f = !0;
		var a = H.shouldComponentUpdate, o = H.componentWillUpdate;
		H.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, H.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function G(e, t) {
	var n = Be(V++, 3);
	!U.__s && Je(n.__H, t) && (n.__ = e, n.u = t, H.__H.__h.push(n));
}
function K(e, t) {
	var n = Be(V++, 4);
	!U.__s && Je(n.__H, t) && (n.__ = e, n.u = t, H.__h.push(n));
}
function q(e) {
	return Me = 5, He(function() {
		return { current: e };
	}, []);
}
function He(e, t) {
	var n = Be(V++, 7);
	return Je(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Ue() {
	for (var e; e = Ne.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Ke), t.__h.some(qe), t.__h = [];
		} catch (n) {
			t.__h = [], U.__e(n, e.__v);
		}
	}
}
U.__b = function(e) {
	H = null, Pe && Pe(e);
}, U.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), ze && ze(e, t);
}, U.__r = function(e) {
	Fe && Fe(e), V = 0;
	var t = (H = e.__c).__H;
	t && (Ae === H ? (t.__h = [], H.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Ke), t.__h.some(qe), t.__h = [], V = 0)), Ae = H;
}, U.diffed = function(e) {
	Ie && Ie(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Ne.push(t) !== 1 && je === U.requestAnimationFrame || ((je = U.requestAnimationFrame) || Ge)(Ue)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ae = H = null;
}, U.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Ke), e.__h = e.__h.filter(function(e) {
				return !e.__ || qe(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], U.__e(n, e.__v);
		}
	}), Le && Le(e, t);
}, U.unmount = function(e) {
	Re && Re(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Ke(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && U.__e(t, n.__v));
};
var We = typeof requestAnimationFrame == "function";
function Ge(e) {
	var t, n = function() {
		clearTimeout(r), We && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	We && (t = requestAnimationFrame(n));
}
function Ke(e) {
	var t = H, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), H = t;
}
function qe(e) {
	var t = H;
	e.__c = e.__(), H = t;
}
function Je(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function Ye(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var Xe = 0;
Array.isArray;
function J(e, t, n, r, i, a) {
	t ||= {};
	var o, s, c = t;
	if ("ref" in c) for (s in c = {}, t) s == "ref" ? o = t[s] : c[s] = t[s];
	var l = {
		type: e,
		props: c,
		key: n,
		ref: o,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --Xe,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return b.vnode && b.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function Ze({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1, disabled: s = !1 }) {
	return /* @__PURE__ */ J("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ J("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ J("input", {
				id: e,
				class: "geist-input",
				type: "password",
				autoComplete: o ? "current-password" : "new-password",
				maxLength: 256,
				value: n,
				onInput: (e) => r(e.currentTarget.value),
				required: !s,
				disabled: s,
				"aria-invalid": !!i,
				"aria-describedby": i || a ? `${e}-hint` : void 0
			}),
			i || a ? /* @__PURE__ */ J("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function Qe({ initial: e, receipt: t }) {
	let [n, r] = W(e), [a, s] = W(""), [c, l] = W(""), [d, f] = W(""), [p, m] = W(!1), [h, g] = W(""), [_, v] = W({}), y = q(null), b = q(!1), x = q(null);
	return /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-fieldset-type": p ? "warning" : void 0,
		onSubmit: async (e) => {
			if (e.preventDefault(), b.current) return;
			g("");
			let i = {};
			if (n.mode === "password" && !a && (i.current_password = "请输入当前访问密码"), p || ((c.length < 8 || c.length > 256) && (i.password = "访问密码需为 8–256 个字符"), c !== d && (i.confirmation = "两次输入的密码不一致")), v(i), Object.keys(i).length) {
				requestAnimationFrame(() => y.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			b.current = !0, u(x.current, !0);
			try {
				let e = await B("/api/configuration/access", {
					revision: n.revision,
					action: p ? "disable" : "set",
					confirm_disable: p,
					current_password: a,
					password: p ? "" : c,
					confirmation: p ? "" : d
				});
				r(e), s(""), l(""), f(""), m(!1), v({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof Oe ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? v(n) : g(R(e));
			} finally {
				b.current = !1, u(x.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: y,
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("accessTitle", "访问密码") } }), /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: n.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : n.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : n.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
					})]
				}),
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ J("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ J("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ J("input", {
							type: "checkbox",
							checked: p,
							onChange: (e) => m(e.currentTarget.checked)
						}), /* @__PURE__ */ J("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ J("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ J("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ J(Ze, {
					id: "access-current",
					label: "当前访问密码",
					value: a,
					onInput: s,
					error: _.current_password,
					current: !0
				}) : null,
				n.mode === "locked" ? null : /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J(Ze, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: c,
					onInput: l,
					disabled: p,
					error: p ? void 0 : _.password,
					help: p ? "关闭访问密码时无需填写。" : "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ J(Ze, {
					id: "access-confirm",
					label: "确认访问密码",
					value: d,
					onInput: f,
					disabled: p,
					error: p ? void 0 : _.confirmation
				})] }),
				p && /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: o("保存后，能连接到 Peach 的设备将直接访问馆藏。", {
					variant: "warning",
					label: "访问范围"
				}) } }),
				h ? /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: h
				}) : null
			]
		}), n.mode === "locked" ? null : /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ J("p", { children: "保存后立即生效。" }), /* @__PURE__ */ J("button", {
				class: "geist-button primary",
				type: "submit",
				ref: x,
				children: "保存配置"
			})]
		})]
	});
}
//#endregion
//#region src/islands/release-updates.tsx
var $e = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function et({ initial: e, initialJob: t }) {
	let [r, a] = W(e), [o, c] = W(t || {
		state: "idle",
		progress: 0
	}), [l, d] = W(""), f = q(null), p = q(!0), m = q(!1), h = q(null);
	G(() => {
		u(h.current, $e.has(o.state));
	}, [o.state]), G(() => () => {
		p.current = !1, f.current?.abort();
	}, []);
	let g = async () => {
		let e = await B("/api/configuration/update-restart", {});
		p.current && c(e);
	};
	G(() => {
		o.state !== "ready" || m.current || (m.current = !0, n({
			title: "更新已准备好",
			body: `Peach ${o.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: g
		}));
	}, [o.state]), G(() => {
		if (!$e.has(o.state)) return;
		let e = new AbortController(), t, n = 0, r = async () => {
			try {
				let t = await z("/api/configuration/update-status", e.signal);
				e.signal.aborted || (c(t), n = 0, t.state === "complete" && a((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				})));
			} catch {
				++n >= 120 && !e.signal.aborted && d("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && n < 120 && (t = setTimeout(r, 1e3));
		};
		return t = setTimeout(r, 1e3), () => {
			e.abort(), clearTimeout(t);
		};
	}, [o.state]);
	let _ = async (e) => {
		if (f.current || $e.has(o.state)) return;
		let t = new AbortController();
		f.current = t, m.current = !1, d(""), u(e, !0);
		try {
			let e = await B("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || c(e);
		} catch (e) {
			t.signal.aborted || d(R(e));
		} finally {
			f.current = null, u(e, !1);
		}
	}, v = async (t) => {
		if (f.current) return;
		let n = new AbortController();
		f.current = n, u(t, !0), d("");
		try {
			let e = await z("/api/configuration/updates", n.signal);
			n.signal.aborted || a(e);
		} catch (t) {
			n.signal.aborted || (a({
				...e,
				state: "error"
			}), d(R(t)));
		} finally {
			f.current = null, u(t, !1);
		}
	};
	return /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ J("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ J("dt", { children: "当前版本" }),
						/* @__PURE__ */ J("dd", { children: r.current_version }),
						/* @__PURE__ */ J("dt", { children: "安装方式" }),
						/* @__PURE__ */ J("dd", { children: r.installation }),
						/* @__PURE__ */ J("dt", { children: "更新通道" }),
						/* @__PURE__ */ J("dd", { children: r.channel }),
						/* @__PURE__ */ J("dt", { children: "最新版本" }),
						/* @__PURE__ */ J("dd", { children: r.latest_version || (r.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				/* @__PURE__ */ J("p", {
					class: l || r.state === "error" ? "configbad" : "confighelp",
					role: l || r.state === "error" ? "alert" : "status",
					children: l || r.message
				}),
				o.state === "idle" ? null : /* @__PURE__ */ J("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ J("p", {
						class: o.state === "error" ? "configbad" : "confighelp",
						children: o.message
					}), o.state === "error" ? null : /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: s(o.state === "downloading" ? "下载进度" : "安装进度", o.state === "downloading" ? o.downloaded || 0 : o.progress, o.state === "downloading" ? o.total || 1 : 100) } }), /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: o.state === "downloading" && o.total ? `${((o.downloaded || 0) / 1048576).toFixed(1)} / ${(o.total / 1048576).toFixed(1)} MB` : `${o.progress}%`
					})] })]
				})
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ J("a", {
					class: "geist-button",
					href: r.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: ["查看发布页", /* @__PURE__ */ J("svg", {
						"aria-hidden": "true",
						viewBox: "0 0 24 24",
						children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
					})]
				}),
				o.state === "ready" ? /* @__PURE__ */ J("button", {
					type: "button",
					class: "geist-button primary",
					onClick: () => {
						n({
							title: "更新已准备好",
							body: `Peach ${o.version || ""} 将在重启后安装。`,
							confirmLabel: "立即重启",
							cancelLabel: "稍后",
							onConfirm: g
						});
					},
					children: "重启安装"
				}) : null,
				r.state === "available" && r.installation === "独立测试包" && o.state !== "ready" ? /* @__PURE__ */ J("button", {
					ref: h,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => _(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ J("button", {
					type: "button",
					class: "geist-button",
					disabled: $e.has(o.state),
					onClick: (e) => v(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function tt({ initial: e, receipt: t }) {
	let [n, r] = W(e), [a, o] = W(e.mode), [s, l] = W(""), [d, p] = W(""), m = q(!1), h = q(null), g = q(null), _ = q(new AbortController());
	G(() => () => _.current.abort(), []), K(() => {
		let t = h.current;
		t.innerHTML = c([
			["environment", "系统代理"],
			["direct", "直连"],
			["proxy", "自定义"]
		], e.mode, {
			label: "Peach 代理",
			className: "configselect",
			attr: "data-fixed-width"
		});
		let n = f(t.firstElementChild), r = () => o(n.value);
		return n.addEventListener("change", r), () => {
			n.removeEventListener("change", r), t.replaceChildren();
		};
	}, []);
	async function v() {
		if (!m.current) {
			m.current = !0, u(g.current, !0), p("");
			try {
				let e = await B("/api/configuration/peach-proxy", {
					mode: a,
					proxy: s
				}, "POST", _.current.signal);
				_.current.signal.aborted || (r(e), l(""), t("已保存 Peach 代理"));
			} catch (e) {
				_.current.signal.aborted || p(R(e));
			} finally {
				m.current = !1, u(g.current, !1);
			}
		}
	}
	return /* @__PURE__ */ J("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), v();
		},
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("peachProxyTitle", "Peach 代理") } }), /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: "采集来源选择“Peach 代理”时共用此设置。"
					})]
				}),
				/* @__PURE__ */ J("div", { ref: h }),
				a === "proxy" && /* @__PURE__ */ J("div", {
					class: "configfield",
					children: [/* @__PURE__ */ J("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ J("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: s,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => l(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ J("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				d && /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: d
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				ref: g,
				class: "geist-button primary",
				type: "submit",
				children: "保存代理"
			})
		})]
	});
}
//#endregion
//#region src/islands/desktop-settings.tsx
function nt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ J("label", {
		class: "configcheck",
		children: [/* @__PURE__ */ J("span", {
			class: "pcheck",
			children: [/* @__PURE__ */ J("input", {
				type: "checkbox",
				checked: t,
				disabled: n,
				onChange: (e) => r(e.currentTarget.checked)
			}), /* @__PURE__ */ J("span", {
				"aria-hidden": "true",
				children: /* @__PURE__ */ J("svg", {
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ J("use", { href: "#i-check" })
				})
			})]
		}), /* @__PURE__ */ J("span", { children: e })]
	});
}
function rt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ J("label", {
		class: "configtoggle",
		children: [/* @__PURE__ */ J("span", { children: e }), /* @__PURE__ */ J("input", {
			class: "ptoggle",
			type: "checkbox",
			role: "switch",
			checked: t,
			disabled: n,
			onChange: (e) => r(e.currentTarget.checked)
		})]
	});
}
function it({ startup: e, receipt: t }) {
	let [n, r] = W(e.enabled), [a, o] = W(e.silent), [s, c] = W(""), l = q(!1), d = q(null);
	async function f() {
		if (!l.current) {
			l.current = !0, u(d.current, !0), c("");
			try {
				await B("/api/configuration/startup", {
					enabled: n,
					silent: a
				}), t("已保存开机自启");
			} catch (e) {
				c(R(e));
			} finally {
				l.current = !1, u(d.current, !1);
			}
		}
	}
	return /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), f();
		},
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("startupTitle", "开机自启") } }),
				/* @__PURE__ */ J("div", {
					class: "configoptions",
					role: "group",
					"aria-labelledby": "startupTitle",
					children: [/* @__PURE__ */ J(rt, {
						label: "开机后启动 Peach",
						checked: n,
						disabled: !e.available,
						change: r
					}), /* @__PURE__ */ J("div", {
						class: "configoption",
						children: [/* @__PURE__ */ J(rt, {
							label: "静默启动",
							checked: a,
							disabled: !e.available,
							change: o
						}), /* @__PURE__ */ J("p", {
							class: "confighelp",
							children: "静默启动仅显示托盘。"
						})]
					})]
				}),
				e.message && /* @__PURE__ */ J("p", {
					class: "confighelp",
					children: e.message
				}),
				s && /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: s
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				ref: d,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存配置"
			})
		})]
	});
}
function at({ data: e }) {
	let t = q(null);
	return K(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let i = document.createElement("summary");
		i.innerHTML = v("chevron-right") + "<span>数据目录</span>", r.append(i);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), d(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ J("div", { ref: t });
}
function ot({ uninstall: e }) {
	let [t, r] = W(!1), [a, o] = W("");
	async function s() {
		await n({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序和开机自启。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await B("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				o(e.message);
			}
		});
	}
	return /* @__PURE__ */ J("section", {
		id: "uninstallPeach",
		class: "configfieldset configdanger",
		"data-geist-fieldset": !0,
		"data-fieldset-type": "error",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("uninstallTitle", "卸载 Peach") } }), e.available && /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: "卸载会退出 Peach、移除程序和开机自启。原始媒体文件保留。"
					})]
				}),
				/* @__PURE__ */ J(nt, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!a,
					change: r
				}),
				/* @__PURE__ */ J(at, { data: e }),
				e.message && /* @__PURE__ */ J("p", {
					class: "confighelp",
					children: e.message
				}),
				a && /* @__PURE__ */ J("p", {
					class: "confighelp",
					role: "status",
					children: a
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				type: "button",
				class: "geist-button danger",
				disabled: !e.available || !!a,
				onClick: () => void s(),
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/islands/configuration.tsx
var st = "/api/configuration", ct = "/api/pick-folder", lt = 8e3, ut = (e, t) => z(st, t), Y = ({ html: e, class: t }) => /* @__PURE__ */ J("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), dt = (e) => !(e instanceof Oe) || e.status !== 400 ? null : e.body?.errors ?? null;
function ft({ facts: e }) {
	return /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ J(Y, { html: i("configFactsTitle", "运行信息") }), /* @__PURE__ */ J("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("dt", { children: e.term }), /* @__PURE__ */ J("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ J("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ J("a", {
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ J("svg", {
							"aria-hidden": "true",
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function pt({ data: t }) {
	let [n, r] = W(t.media_sources), [a, o] = W(""), s = q(null);
	G(() => () => s.current?.abort(), []);
	let c = async (e) => {
		if (s.current) return;
		let t = new AbortController();
		s.current = t, u(e, !0), o("");
		try {
			let e = await z(st, t.signal);
			t.signal.aborted || r(e.media_sources);
		} catch (e) {
			t.signal.aborted || o(R(e));
		} finally {
			s.current = null, u(e, !1);
		}
	};
	return n ? /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J(Y, { html: i("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ J("dl", {
					class: "configfacts",
					children: n.map((t) => /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("dt", { children: [/* @__PURE__ */ J("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: l(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ J("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ J("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				a ? /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: a
				}) : null
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => c(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function mt({ value: t, label: n, onChange: r }) {
	let i = q(null), a = q(null), o = q(r);
	return o.current = r, K(() => {
		let r = i.current;
		r.innerHTML = c([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([t, n]) => [
			t,
			n,
			e[t]
		]), t, { label: n });
		let s = f(r.firstElementChild);
		a.current = s;
		let l = () => o.current(s.value);
		return s.addEventListener("change", l), () => {
			a.current = null, s.disabled = !0, s.removeEventListener("change", l), r.replaceChildren();
		};
	}, [n]), K(() => {
		a.current && (a.current.value = t);
	}, [t]), /* @__PURE__ */ J("div", {
		ref: i,
		class: "configsourcecontrol"
	});
}
function ht({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, a] = W(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [s, c] = W(n?.map((e) => e.location) ?? []), [l, d] = W(n?.map((e) => e.root) ?? []), [f, p] = W(String(e.port)), [m, h] = W(!1), [g, _] = W([]), [v, y] = W(""), [b, x] = W(""), [S, C] = W(null), [w, T] = W(null), E = q(!1), D = q(e.revision), O = q([]), k = q(null);
	K(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), G(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), lt);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		a((n) => n.map((n, r) => r === e ? t : n));
	}, ee = () => {
		T(r.length), a((e) => [...e, ""]);
	}, j = (e) => {
		c((t) => t.filter((t, n) => n !== e)), d((t) => t.filter((t, n) => n !== e)), a((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, M = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, N = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			u(t, !0);
			try {
				let { path: t } = await B(ct, { initial: r[e] ?? "" });
				t && (A(e, t), M(e, ""));
			} catch (t) {
				M(e, R(t));
			} finally {
				u(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ J("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ J("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ J("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ J("use", { href: "#i-check" })
			}), /* @__PURE__ */ J("p", { children: /* @__PURE__ */ J("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ J("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !E.current) {
				E.current = !0, u(k.current, !0), x("");
				try {
					let n = await B(st, {
						revision: D.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: s[t] || "local",
							root: l[t] || ""
						})) } : {},
						port: f,
						scan_now: m
					});
					D.current = n.revision, _([]), y(""), t("已保存配置"), C(n);
				} catch (e) {
					let t = dt(e);
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(R(e)));
				} finally {
					E.current = !1, u(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J(Y, { html: i("configTitle", "这台电脑") }),
				/* @__PURE__ */ J("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ J("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ J("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: r.map((t, n) => /* @__PURE__ */ J("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ J("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ J("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": g[n] ? "true" : void 0,
										onInput: (e) => A(n, e.currentTarget.value),
										ref: (e) => {
											O.current[n] = e;
										}
									}),
									/* @__PURE__ */ J("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => N(n, e.currentTarget),
										children: /* @__PURE__ */ J("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ J("use", { href: "#i-folder-search" })
										})
									}),
									r.length > 1 ? /* @__PURE__ */ J("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => j(n),
										children: /* @__PURE__ */ J("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ J("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ J("div", {
										class: "configsource",
										children: [/* @__PURE__ */ J("div", {
											class: "configsourcelabel",
											children: ["媒体来源", /* @__PURE__ */ J(mt, {
												label: `媒体来源 ${n + 1}`,
												value: s[n] || "local",
												onChange: (e) => {
													let t = [...s];
													t[n] = e, c(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ J("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ J("input", {
											class: "geist-input",
											"aria-label": `Windows 中的对应路径 ${n + 1}`,
											value: l[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...l];
												t[n] = e.currentTarget.value, d(t);
											}
										})] }) : null]
									}),
									g[n] ? /* @__PURE__ */ J("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ J("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: ee,
							children: "添加文件夹"
						}),
						s.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ J("p", {
							class: "confighelp",
							children: ["先在 CloudDrive 登录网盘并完成挂载。", /* @__PURE__ */ J("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: ["挂载帮助", /* @__PURE__ */ J("svg", {
									"aria-hidden": "true",
									viewBox: "0 0 24 24",
									children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
								})]
							})]
						}) : null,
						s.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ J("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ J("a", {
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ J("svg", {
											"aria-hidden": "true",
											viewBox: "0 0 24 24",
											children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ J("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ J("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ J("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ J("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ J("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ J("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ J("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ J("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ J("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ J("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ J("span", { children: "保存后扫描并补全资料" })]
				}),
				b ? /* @__PURE__ */ J(Y, { html: o(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ J("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ J("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function gt({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ J(Y, {
		class: "configpage",
		html: o(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ J("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "通用"
			}) : null,
			t.startup ? /* @__PURE__ */ J(it, {
				startup: t.startup,
				receipt: e
			}) : null,
			/* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			t.editable ? /* @__PURE__ */ J(ht, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ J(Y, { html: o(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ J(pt, { data: t }),
			t.peach_proxy || t.access ? /* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy ? /* @__PURE__ */ J(tt, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ J(Qe, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			t.updates ? /* @__PURE__ */ J(et, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ J(ft, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ J(ot, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var _t = Symbol.for("preact-signals");
function vt() {
	if (Z > 1) Z--;
	else {
		var e, t = !1;
		for ((function() {
			var e = Et;
			for (Et = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); St !== void 0;) {
			var n = St;
			for (St = void 0, Ct++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && At(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (Ct = 0, Z--, t) throw e;
	}
}
function yt(e) {
	if (Z > 0) return e();
	Tt = ++wt, Z++;
	try {
		return e();
	} finally {
		vt();
	}
}
var bt, X = void 0;
function xt(e) {
	var t = X, n = bt;
	X = void 0, bt = void 0;
	try {
		return e();
	} finally {
		X = t, bt = n;
	}
}
var St = void 0, Z = 0, Ct = 0, wt = 0, Tt = 0, Et = void 0, Dt = 0;
function Ot(e) {
	if (X !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== X) return t = {
			i: 0,
			S: e,
			p: X.s,
			n: void 0,
			t: X,
			e: void 0,
			x: void 0,
			r: t
		}, X.s !== void 0 && (X.s.n = t), X.s = t, e.n = t, 32 & X.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = X.s, t.n = void 0, X.s.n = t, X.s = t), t;
	}
}
function Q(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Q.prototype.brand = _t, Q.prototype.h = function() {
	return !0;
}, Q.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? xt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Q.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && xt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Q.prototype.subscribe = function(e) {
	var t = this;
	return Rt(function() {
		var n = t.value;
		xt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Q.prototype.valueOf = function() {
	return this.value;
}, Q.prototype.toString = function() {
	return this.value + "";
}, Q.prototype.toJSON = function() {
	return this.value;
}, Q.prototype.peek = function() {
	var e = this;
	return xt(function() {
		return e.value;
	});
}, Object.defineProperty(Q.prototype, "value", {
	get: function() {
		var e = Ot(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (Ct > 100) throw Error("Cycle detected");
			(function(e) {
				Z !== 0 && Ct === 0 && e.l !== Tt && (e.l = Tt, Et = {
					S: e,
					v: e.v,
					i: e.i,
					o: Et
				});
			})(this), this.v = e, this.i++, Dt++, Z++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				vt();
			}
		}
	}
});
function kt(e, t) {
	return new Q(e, t);
}
function At(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function jt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Mt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function $(e, t) {
	Q.call(this, void 0, t), this.x = e, this.s = void 0, this.g = Dt - 1, this.f = 4;
}
$.prototype = new Q(), $.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === Dt)) return !0;
	if (this.g = Dt, this.f |= 1, this.i > 0 && !At(this)) return this.f &= -2, !0;
	var e = X;
	try {
		jt(this), X = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return X = e, Mt(this), this.f &= -2, !0;
}, $.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Q.prototype.S.call(this, e);
}, $.prototype.U = function(e) {
	if (this.t !== void 0 && (Q.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, $.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty($.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = Ot(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function Nt(e, t) {
	return new $(e, t);
}
function Pt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		Z++;
		var n = X;
		X = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, Ft(e), t;
		} finally {
			X = n, vt();
		}
	}
}
function Ft(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Pt(e);
}
function It(e) {
	if (X !== this) throw Error("Out-of-order effect");
	Mt(this), X = e, this.f &= -2, 8 & this.f && Ft(this), vt();
}
function Lt(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, bt && bt.push(this);
}
Lt.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Lt.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Pt(this), jt(this), Z++;
	var e = X;
	return X = this, It.bind(this, e);
}, Lt.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = St, St = this);
}, Lt.prototype.d = function() {
	this.f |= 8, 1 & this.f || Ft(this);
}, Lt.prototype.dispose = function() {
	this.d();
};
function Rt(e, t) {
	var n = new Lt(e, t);
	try {
		n.c();
	} catch (e) {
		throw n.d(), e;
	}
	var r = n.d.bind(n);
	return r[Symbol.dispose] = r, r;
}
//#endregion
//#region node_modules/@preact/signals/dist/signals.module.js
var zt, Bt, Vt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Ht = [];
Rt(function() {
	zt = this.N;
})();
function Ut(e, t) {
	b[e] = t.bind(null, b[e] || function() {});
}
function Wt(e) {
	if (Bt) {
		var t = Bt;
		Bt = void 0, t();
	}
	Bt = e && e.S();
}
function Gt(e) {
	var t = this, n = e.data, r = qt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = He(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = Nt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = Nt(function() {
			return !Array.isArray(i.value) && !S(i.value);
		}), o = Rt(function() {
			if (this.N = Xt, a.value) {
				var t = i.value;
				e.__v && e.__v.__e && e.__v.__e.nodeType === 3 && (e.__v.__e.data = t);
			}
		}), s = t.__$u.d;
		return t.__$u.d = function() {
			o(), s.call(this);
		}, [a, i];
	}, []), a = i[0], o = i[1];
	return a.value ? o.peek() : o.value;
}
Gt.displayName = "ReactiveTextNode", Object.defineProperties(Q.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Gt
	},
	props: {
		configurable: !0,
		get: function() {
			var e = this;
			return { data: { get value() {
				return e.value;
			} } };
		}
	},
	__b: {
		configurable: !0,
		value: 1
	}
}), Ut("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Q && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Ut("__r", function(e, t) {
	if (e(t), t.type !== I) {
		Wt();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Rt(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				Vt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Wt(n);
	}
}), Ut("__e", function(e, t, n, r) {
	Wt(), e(t, n, r);
}), Ut("diffed", function(e, t) {
	Wt();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Kt(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Kt(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = kt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Rt(function() {
			this.N = Xt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Ut("unmount", function(e, t) {
	if (typeof t.type == "string") {
		var n = t.__e;
		if (n) {
			var r = n.U;
			if (r) for (var i in n.U = void 0, r) {
				var a = r[i];
				a && a.d();
			}
		}
		var o = t.__np;
		if (o) {
			var s = t.props;
			for (var c in o) s[c] = o[c];
		}
		t.__np = void 0;
	} else {
		var l = t.__c;
		if (l) {
			var u = l.__$u;
			u && (l.__$u = void 0, u.d());
		}
	}
	e(t);
}), Ut("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), oe.prototype.shouldComponentUpdate = function(e, t) {
	if (this.__R) return !0;
	var n = this.__$u, r = n && n.s !== void 0;
	for (var i in t) return !0;
	if (this.__f || typeof this.u == "boolean" && !0 === this.u) {
		var a = 2 & this.__$f;
		if (!(r || a || 4 & this.__$f) || 1 & this.__$f) return !0;
	} else if (!(r || 4 & this.__$f) || 3 & this.__$f) return !0;
	for (var o in e) if (o !== "__source" && e[o] !== this.props[o]) return !0;
	for (var s in this.props) if (!(s in e)) return !0;
	return !1;
};
function qt(e, t) {
	return He(function() {
		return kt(e, t);
	}, []);
}
var Jt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Yt() {
	yt(function() {
		for (var e; e = Ht.shift();) zt.call(e);
	});
}
function Xt() {
	Ht.push(this) === 1 && (b.requestAnimationFrame || Jt)(Yt);
}
//#endregion
//#region src/state/quality-goals.ts
var Zt = "/api/quality-goals?limit=200", Qt = {
	data: null,
	error: ""
}, $t = kt(Qt), en = 0, tn = Nt(() => $t.value);
Nt(() => $t.value.data?.total ?? null);
function nn() {
	en += 1, $t.value = Qt;
}
async function rn(e) {
	let t = en += 1;
	try {
		let n = await z(Zt, e);
		return t === en && ($t.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === en && ($t.value = {
			data: null,
			error: R(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var an = (e, t) => rn(t), on = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function sn({ openItem: e, javTitleHtml: t, javDisplayName: n, srcBadge: i }) {
	let { data: a, error: s } = tn.value;
	if (s) return /* @__PURE__ */ J("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: o(s, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let c = a?.items ?? [];
	return c.length ? /* @__PURE__ */ J("div", {
		class: "qualitylist",
		children: c.map((r) => /* @__PURE__ */ J("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ J("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${n(r)}`,
				onClick: () => e(r.id),
				children: /* @__PURE__ */ J("img", {
					src: on(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ J("div", { children: [
				/* @__PURE__ */ J("h3", { children: /* @__PURE__ */ J("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(r.id),
					dangerouslySetInnerHTML: { __html: t(r) }
				}) }),
				/* @__PURE__ */ J("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ J("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: i(r.location, r.cost) }
						}),
						/* @__PURE__ */ J("span", { children: p[r.location] ?? r.location }),
						/* @__PURE__ */ J("span", { children: g(r.duration) }),
						/* @__PURE__ */ J("span", { children: _(r.size ?? 0) })
					]
				}),
				r.reason ? /* @__PURE__ */ J("p", { children: r.reason }) : null
			] })]
		}, r.id))
	}) : /* @__PURE__ */ J("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function cn(e) {
	let t = e.pause || ((e) => new Promise((t) => setTimeout(t, e))), n = 0;
	for (; e.active();) {
		let r;
		try {
			r = await e.read(AbortSignal.timeout(15e3));
		} catch (r) {
			if (!e.active()) return;
			n++, e.disconnected(r), await t(Math.min(2e3 * 2 ** Math.min(n, 4), 3e4));
			continue;
		}
		if (!e.active() || (n = 0, e.render(r), e.once) || !e.keepWatching && r.status !== "running") return;
		await t(2e3);
	}
}
function ln(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	cn({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (e.title || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
				t.innerHTML = e.container ? e.container(c) : c;
			} else if (r && r === a.job_id) r = void 0, i = !0, e.host.hidden = a.status !== "failed", sessionStorage.removeItem(n), t.innerHTML = a.status === "failed" ? e.note(a.error || "检查失败") : "", e.complete(a);
			else {
				if (r && a.status === "idle") {
					e.host.hidden = !1, t.innerHTML = e.note("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(n), i = !0;
					return;
				}
				t.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, t.innerHTML = e.note("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/islands/scraping.tsx
var un = (e, t) => z("/api/scraping", t);
function dn({ value: e, onChange: t }) {
	let n = q(null), r = q(t);
	return r.current = t, K(() => {
		let t = n.current;
		t.innerHTML = c([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = f(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ J("div", {
		ref: n,
		class: "scraping-network"
	});
}
function fn({ source: e, toast: t }) {
	let [n, r] = W(e), [a, s] = W(e.network), [c, l] = W(""), [d, f] = W(""), [p, m] = W("paste"), [g, _] = W(""), [v, y] = W(!1), [b, x] = W(""), [S, C] = W([]), w = q(null), T = q(null);
	K(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => u(e, v));
	}, [v]);
	let E = q(new AbortController());
	G(() => () => E.current.abort(), []);
	async function D(n) {
		if (!v) {
			y(!0), x(""), C([]);
			try {
				if (n === "check") {
					let t = await B("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let i = await B("/api/scraping/settings", {
						source: e.source,
						network: a,
						cookie: c,
						cookies_text: d,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (r(i.saved), l(""), f(""), _(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				E.current.signal.aborted || x(R(e));
			} finally {
				E.current.signal.aborted || y(!1);
			}
		}
	}
	return /* @__PURE__ */ J("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ J("form", {
			ref: T,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), D("save");
			},
			children: [/* @__PURE__ */ J("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ J("div", {
						class: "geist-fieldset-heading",
						children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ J("a", {
							class: "scraping-url",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: [
								/* @__PURE__ */ J("img", {
									src: h(e.login),
									alt: "",
									width: "16",
									height: "16",
									loading: "lazy",
									onError: (e) => e.currentTarget.remove()
								}),
								/* @__PURE__ */ J("span", { children: e.login }),
								/* @__PURE__ */ J("svg", {
									"aria-hidden": "true",
									children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
								})
							]
						})]
					}),
					/* @__PURE__ */ J("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ J(dn, {
							value: a,
							onChange: s
						})]
					}),
					a === "peach" && /* @__PURE__ */ J("a", {
						class: "geist-text-link",
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ J(I, { children: [
						/* @__PURE__ */ J("p", { children: n.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ J("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ J("label", { children: [/* @__PURE__ */ J("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: p === t,
								onChange: () => {
									m(t), l(""), f(""), _("");
								}
							}), /* @__PURE__ */ J("span", { children: n })] }, t))
						}),
						p === "paste" ? /* @__PURE__ */ J("label", { children: ["Cookie", /* @__PURE__ */ J("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: c,
							disabled: v,
							onInput: (e) => l(e.currentTarget.value)
						})] }) : /* @__PURE__ */ J("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ J("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ J("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ J("span", {
										class: "scraping-file-name",
										children: g || "未选择文件"
									}),
									/* @__PURE__ */ J("input", {
										ref: w,
										type: "file",
										accept: ".txt",
										disabled: v,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												f(""), _("");
												return;
											}
											if (f(""), t.size > 262144) {
												x("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											y(!0);
											try {
												let e = await t.text();
												E.current.signal.aborted || (f(e), _(t.name));
											} catch {
												E.current.signal.aborted || x("Cookie 文件未读取，请重新选择");
											} finally {
												E.current.signal.aborted || y(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					b && /* @__PURE__ */ J("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: o(b, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ J("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: o(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ J("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ J("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("revoke"),
						children: "撤销 Cookie"
					}),
					/* @__PURE__ */ J("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("check"),
						children: "检查连接"
					}),
					/* @__PURE__ */ J("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					})
				]
			})]
		})
	});
}
function pn({ data: e, error: t, toast: n }) {
	let [r, a] = W(""), [s, c] = W(!1), [l, d] = W(""), f = q(null);
	K(() => u(f.current, s), [s]);
	let p = q(new AbortController()), m = q(0);
	async function h(e = !1) {
		let t = ++m.current;
		await cn({
			read: (e) => z("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				c(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	G(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!s) {
			m.current++, c(!0), d("");
			try {
				await B("/api/scraping/cover", { code: r }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (c(!1), d(R(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ J("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: o(t, { variant: "error" }) }
	}) : /* @__PURE__ */ J("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ J("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ J("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ J("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ J("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ J("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: s,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => a(e.currentTarget.value)
							}), /* @__PURE__ */ J("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						l && /* @__PURE__ */ J("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: o(l, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ J(fn, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var mn = (e, t) => z("/api/library-processing", t);
function hn({ data: e, error: t, toast: n, onComplete: r, mode: c, monitor: l }) {
	let [d, f] = W(e || { status: "idle" }), [p, m] = W(t), [h, g] = W(!1), [_, v] = W(!1), y = q(new AbortController()), b = q(0), x = q(d.status), S = q(null), C = h || d.status === "running";
	K(() => u(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await cn({
			read: (e) => z("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: c === "notice" || !!l,
			render: (e) => {
				f(e), m(""), e.status === "complete" && x.current === "running" && c !== "notice" && (v(!0), n("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => m("连接中断，正在重新读取处理进度")
		});
	}
	G(() => ((d.status === "running" || c === "notice" || l) && w(), () => y.current.abort()), []);
	async function T() {
		if (!C) {
			g(!0), m(""), v(!1);
			try {
				let e = await B("/api/library-processing", {}, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = e.status, f(e), g(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (m(R(e)), g(!1));
			}
		}
	}
	return c === "notice" ? !p && d.status !== "running" && d.status !== "failed" ? null : /* @__PURE__ */ J("div", {
		class: "library-processing-banner",
		role: "status",
		children: [/* @__PURE__ */ J("span", { children: p || (d.status === "failed" ? "扫描与资料采集未完成" : `${d.stage || "正在整理馆藏"}${d.total ? ` · ${d.checked || 0} / ${d.total}` : ""}`) }), /* @__PURE__ */ J("a", {
			class: "geist-button",
			href: "/data-cleanup#libraryProcessing",
			children: p || d.status === "failed" ? "查看并处理" : "查看进度"
		})]
	}) : /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: i("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ J("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ J("div", {
				"aria-live": "polite",
				children: [
					d.status === "running" && /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: a(`${d.stage || "正在处理"}${d.total ? ` · ${d.checked || 0} / ${d.total}` : ""}`) } }), !!d.total && /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: s(`已处理 ${d.checked || 0} / ${d.total} 个视频`, d.checked || 0, d.total) } })] }),
					(p || d.status === "failed") && /* @__PURE__ */ J("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: o(p || d.error || "处理未完成，请重试", { variant: "error" }) }
					}),
					d.status === "failed" && !!d.issues?.length && /* @__PURE__ */ J("ul", { children: d.issues.slice(0, 20).map((e) => /* @__PURE__ */ J("li", { children: [
						e.asset_id ? /* @__PURE__ */ J("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					_ && /* @__PURE__ */ J("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: o(`已扫描 ${d.scanned || 0} 个文件，识别 ${d.identified || 0} 个番号，整理 ${d.candidates || 0} 组资料候选。`, {
							variant: "success",
							label: "处理完成"
						}) }
					})
				]
			})
		]
	}), /* @__PURE__ */ J("footer", {
		class: "geist-fieldset-footer",
		"data-geist-fieldset-footer": !0,
		children: [
			/* @__PURE__ */ J("a", {
				class: "geist-button",
				href: "/scraping",
				children: "采集来源"
			}),
			!!d.candidates && /* @__PURE__ */ J("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			/* @__PURE__ */ J("button", {
				ref: S,
				type: "button",
				class: "geist-button primary",
				onClick: () => void T(),
				children: d.status === "failed" ? "重试未完成项" : "扫描并补全资料"
			})
		]
	})] });
}
//#endregion
//#region src/state/index.ts
var gn = { "quality-goals": {
	refresh: rn,
	reset: nn
} }, _n = () => Object.keys(gn);
async function vn(e) {
	let t = gn[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-evidence.ts
var yn = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function bn(e = "") {
	let t = yn(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${t ? " hidden" : ""}>未取得来源图片</span>${t ? `<img src="${m(t)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function xn(e) {
	let t = yn(e.profile_url), n = (e.preview_assets || []).slice(0, 6), r = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${m(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${t ? `<a class="geist-button" href="${m(t)}" target="_blank" rel="noopener noreferrer">来源资料 ↗</a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${m(e.creator || "")}">查看全部 ${r.toLocaleString()} 部作品</button></div>
    ${bn(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${n.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${n.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${m(e.name)}">${m(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${m(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function Sn(e) {
	for (let t of e.querySelectorAll("[data-review-picture] img")) {
		let e = () => {
			t.hidden = !0;
			let e = t.parentElement?.querySelector(".reviewimageempty");
			e && (e.hidden = !1);
		};
		t.addEventListener("error", e), t.complete && !t.naturalWidth && e();
	}
}
//#endregion
//#region src/review-bulk.ts
var Cn = () => ({
	busy: !1,
	category: "",
	filter: "",
	groupBy: "candidates",
	anchor: null,
	selected: /* @__PURE__ */ new Set(),
	choices: /* @__PURE__ */ new Map(),
	assets: /* @__PURE__ */ new Map(),
	errors: /* @__PURE__ */ new Map()
});
function wn(e, t) {
	let n = [[
		"candidates",
		t ? "按候选数量" : "全部待复核",
		"list-filter"
	]];
	return e.some((e) => e.source || e.candidates?.some((e) => e.source)) && n.push([
		"source",
		"按来源",
		"list-filter"
	]), e.some((e) => e.field) && n.push([
		"field",
		"按字段",
		"list-filter"
	]), n;
}
function Tn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r of e) {
		let e, i;
		if (t === "field") e = r.field || "__unspecified_field", i = r.field_label || r.field || "未标注字段";
		else if (t === "source") {
			let t = [...new Set((r.candidates?.map((e) => e.source || "") || [r.source || ""]).filter(Boolean))].sort();
			e = JSON.stringify(t), i = t.join(" / ") || "未标注来源";
		} else e = r.candidates ? r.candidates.length === 1 ? "single" : "multiple" : "pending", i = e === "single" ? "单一候选" : e === "multiple" ? "需选择来源" : "待复核";
		n.has(e) || n.set(e, {
			key: e,
			title: i,
			rows: []
		}), n.get(e).rows.push(r);
	}
	return [...n.values()];
}
function En(e, t, n, r, i) {
	let a = e.anchor === null ? -1 : t.indexOf(e.anchor), o = t.indexOf(n);
	r && a >= 0 && o >= 0 ? t.slice(Math.min(a, o), Math.max(a, o) + 1).forEach((t) => e.selected.add(t)) : i ? e.selected.add(n) : e.selected.delete(n), e.anchor = n;
}
async function Dn(e, t, n, r) {
	let i = [], a = 0;
	for (let o of e) {
		if (!r()) break;
		try {
			let e = await t(o.payload);
			if (!e.ok) throw Error(e.error || "服务端未采用该项");
			a++, n(o.key);
		} catch (e) {
			i.push({
				key: o.key,
				message: R(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function On(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function kn(e, n) {
	let r = e.querySelector(".reviewlist");
	if (!r || !n.rows.length || n.locked) return;
	let i = n.state, a = [...r.querySelectorAll("[data-review-key]")];
	n.category !== void 0 && i.category !== n.category && (i.category = n.category, i.filter = "", i.groupBy = "candidates", i.anchor = null);
	let o = wn(n.rows, n.metadata);
	o.some((e) => e[0] === i.groupBy) || (i.groupBy = "candidates", i.filter = "");
	let s = Tn(n.rows, i.groupBy);
	s.some((e) => e.key === i.filter) || (i.filter = "");
	let l = () => [...r.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), d = () => l().filter((e) => i.selected.has(e.dataset.reviewKey)), p = () => n.rows.filter((e) => d().some((t) => t.dataset.reviewKey === e.item_key)), m = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, h = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, g = document.createElement("div");
	g.className = "reviewbulkbar reviewbulktoolbar", g.setAttribute("role", "group"), g.setAttribute("aria-label", "复核批量操作");
	let _ = document.createElement("div");
	_.className = "reviewgroupby", _.innerHTML = c(o, i.groupBy, { label: "筛选分组方式" });
	let v = f(_.firstElementChild);
	_.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), v.addEventListener("change", () => {
		if (i.busy || !o.some((e) => e[0] === v.value)) return;
		i.groupBy = v.value, i.filter = "", i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let y = document.createElement("div");
	y.className = "reviewcategoryfilter", y.hidden = s.length < 2, y.innerHTML = c([[
		"",
		"全部分类",
		"list-filter"
	], ...s.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], i.filter, { label: i.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let b = y.querySelector("[data-select-menu]");
	if (b) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", i.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(b.children).slice(1)), b.append(e);
	}
	let x = f(y.firstElementChild);
	y.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), x.addEventListener("change", () => {
		if (i.busy || x.value && !s.some((e) => e.key === x.value)) return;
		i.filter = x.value, i.anchor = null;
		let t = e.parentElement;
		n.refresh(), t?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let S = h("全选本页"), C = h("通过所选", "primary"), w = h("拒绝所选", "error"), T = document.createElement("span");
	T.className = "reviewselectedcount selectiondockcount", T.setAttribute("role", "status");
	let E = document.createElement("div");
	E.className = "reviewbulksource", E.hidden = !n.metadata;
	let D = document.createElement("p");
	D.className = "reviewstate reviewbulkfeedback", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulkdecisions", O.append(C, w);
	let k = document.createElement("div");
	k.className = "selectiondock reviewdock", k.setAttribute("role", "group"), k.setAttribute("aria-label", "复核所选项目");
	let A = h("取消选择");
	k.append(T, E, O, A, D), g.append(_, y, S);
	let ee = e.querySelector(".reviewcontrols");
	ee ? ee.append(g) : r.before(g), e.append(k), r.classList.add("reviewgroups");
	let j = () => {
		i.selected.clear(), i.anchor = null, P();
	};
	A.onclick = () => {
		i.busy || (j(), S.focus({ preventScroll: !0 }));
	}, S.onclick = () => {
		if (i.busy) return;
		let e = l(), t = d().length === e.length;
		e.forEach((e) => t ? i.selected.delete(e.dataset.reviewKey) : i.selected.add(e.dataset.reviewKey)), P();
	}, C.onclick = () => te("approved", C), w.onclick = () => te("rejected", w);
	let M = [];
	for (let e of s) {
		let n = e.rows.map((e) => a.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e), o = document.createElement("section");
		o.className = "reviewgroup", o.hidden = !!i.filter && e.key !== i.filter;
		let s = document.createElement("div");
		s.className = "reviewbulkbar";
		let c = document.createElement("h3");
		c.textContent = `${e.title} · ${n.length}`;
		let u = h("全选本组"), d = document.createElement("div");
		d.className = "reviewlist", s.append(c, u), o.append(s, d), r.append(o), u.onclick = () => {
			if (i.busy) return;
			let e = n.every((e) => i.selected.has(e.dataset.reviewKey));
			n.forEach((t) => e ? i.selected.delete(t.dataset.reviewKey) : i.selected.add(t.dataset.reviewKey)), P();
		}, M.push(() => {
			u.textContent = n.every((e) => i.selected.has(e.dataset.reviewKey)) ? "清空本组" : "全选本组";
		});
		for (let e of n) {
			d.append(e);
			let n = e.dataset.reviewKey;
			i.errors.has(n) && (e.querySelector(".reviewstate").textContent = i.errors.get(n));
			let r = e.querySelector("h4,.reviewentity b") || e, a = document.createElement("label");
			a.className = "reviewpickitem", a.innerHTML = t();
			let o = a.querySelector("input");
			if (o.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || r.textContent || n}`), r !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...r.childNodes), r.classList.add("reviewpickheading"), r.append(a, e);
			} else e.prepend(a);
			let s = (e, t) => {
				En(i, l().map((e) => e.dataset.reviewKey), n, e, t), P();
			};
			if (a.addEventListener("mousedown", (e) => {
				e.shiftKey && e.preventDefault();
			}), a.addEventListener("click", (e) => {
				e.target !== o && (e.preventDefault(), i.busy || (o.focus(), s(e.shiftKey, !o.checked)));
			}), o.addEventListener("click", (e) => {
				i.busy || s(e.shiftKey, o.checked);
			}), o.addEventListener("keydown", (t) => {
				if (!(i.busy || !t.shiftKey)) {
					if (t.key === " ") t.preventDefault(), s(!0, !0);
					else if (t.key === "ArrowDown" || t.key === "ArrowUp") {
						t.preventDefault();
						let r = l(), a = r[r.indexOf(e) + (t.key === "ArrowDown" ? 1 : -1)];
						a && (i.anchor === null && (i.anchor = n), En(i, r.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), P(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), M.push(() => {
				o.checked = i.selected.has(n);
			}), i.assets.has(n)) {
				let t = i.assets.get(n), r = [...e.querySelectorAll("[data-review-asset]")];
				r.forEach((e) => {
					let n = t.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(n)), e.classList.toggle("picked", n);
				});
				let a = e.querySelector("[data-picked-count]");
				a && (a.textContent = `已选 ${t.length} / ${r.length}`);
			}
			e.addEventListener("click", (t) => {
				t.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && i.assets.set(n, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let t of e.querySelectorAll("input[type=\"radio\"]")) i.choices.has(n) && (t.checked = i.choices.get(n) === t.value), t.addEventListener("change", () => {
				t.checked && i.choices.set(n, t.value), P();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		i.busy || !e.contains(r) || (t.key === "Escape" && i.selected.size && (t.preventDefault(), t.stopPropagation(), j()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), l().forEach((e) => i.selected.add(e.dataset.reviewKey)), P()));
	});
	let N = "";
	function P() {
		let e = d();
		S.textContent = e.length === l().length ? "清空当前选择" : i.filter ? "全选当前分类" : "全选本页", k.hidden = !e.length, T.textContent = `已选 ${e.length} 项`, C.disabled = !e.length || e.some((e) => !m(e)), w.disabled = !e.length;
		let t = On(p());
		E.hidden = !n.metadata || !p().some((e) => (e.candidates?.length || 0) > 1);
		let r = e.length && !t.length ? "所选项目无共同来源" : "统一选择来源", a = JSON.stringify([r, t]);
		if (a !== N) {
			N = a, E.innerHTML = c([["", r], ...t.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = f(E.firstElementChild);
			e.disabled = !t.length, e.addEventListener("change", () => {
				if (!(i.busy || !On(p()).includes(e.value))) {
					for (let t of d()) {
						let r = n.rows.find((e) => e.item_key === t.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						t.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === r.candidate_key;
						}), i.choices.set(t.dataset.reviewKey, r.candidate_key);
					}
					D.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		M.forEach((e) => e());
	}
	async function te(t, r) {
		if (i.busy || !d().length) return;
		let a = d().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...n.payload(e),
				status: t
			}
		}));
		if (t === "approved" && n.metadata && a.some((e) => !e.payload.candidate_key)) {
			D.textContent = "请先为所选的多来源候选选择来源。", d().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		i.busy = !0, D.textContent = `正在处理 0 / ${a.length}`, u(r, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let l = 0, f = await Dn(a, async (e) => {
			try {
				return await n.submit(e);
			} finally {
				l++, n.active() && (D.textContent = `正在处理 ${l} / ${a.length}`);
			}
		}, (e) => {
			i.selected.delete(e), i.errors.delete(e), n.applied(e);
		}, n.active);
		if (i.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), u(r, !1), !n.active()) return;
		n.notify(`已${t === "approved" ? "通过" : "拒绝"} ${f.completed} 项${f.failures.length ? `，${f.failures.length} 项未完成` : ""}`), f.failures.forEach((e) => i.errors.set(e.key, e.message));
		let p = e.parentElement;
		n.refresh(), p?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	P();
}
//#endregion
//#region src/native-image.ts
function An(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function jn(e, t, n, r, i = 1) {
	let a = Number.isFinite(i) && i > 0 ? i : 1;
	e /= a, t /= a;
	let o = [
		e,
		t,
		n,
		r
	].every((e) => Number.isFinite(e) && e > 0), s = o && Math.min(n, r) >= 64 && (e < n * .4 || t < r * .4), c = o ? Math.min(1, n / e, r / t) : 1;
	return {
		small: s,
		width: e * c,
		height: t * c
	};
}
//#endregion
//#region src/entity-skeleton.ts
function Mn(e, t) {
	return `<section data-skeleton="entity/${e}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <div class="entityhero"><div class="entityportrait ${e === "studio" || e === "agency" ? "square " : ""}skeleton"></div>
      <div class="entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div>
    <section class="entitytagbar"><div class="entitytags"><span class="skeleton entitymediaskeleton"></span><span class="skeleton entitymediaskeleton"></span></div></section>
    <div class="entitysection">${t}</div></div></section>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var Nn = [
	"loc",
	"creator",
	"performer",
	"studio",
	"series",
	"agency",
	"tag",
	"tag_match",
	"len",
	"dur_min",
	"dur_max",
	"orient",
	"state",
	"jav",
	"thumb"
];
function Pn() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function Fn(e, t) {
	let n = new URLSearchParams();
	for (let t of Nn) e[t] && n.set(t, e[t]);
	let [r, i] = await Promise.all([t("/api/facets?" + n), t("/api/items?" + n + "&limit=5")]), a = [...new Set([
		...r.creators || [],
		...r.tagperformers || [],
		...r.tags || []
	].map((e) => String(e.k || "")).concat((i.items || []).map((e) => e.code || e.name || "")))].filter((e) => e.length > 1).slice(0, 10);
	return (await Promise.all(a.map(async (e) => {
		let r = new URLSearchParams(n);
		return r.set("q", e), r.set("limit", "1"), (await t("/api/items?" + r)).total > 0 ? e : "";
	}))).filter(Boolean);
}
function In({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", s = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	return t || n ? r("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" }) : e === "catalog" ? r("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s }) : r(e === "tags" ? "tags" : "user-round", "还没有" + ({
		tags: "标签",
		performers: "艺人",
		creators: "创作者",
		studios: "厂牌",
		agencies: "事务所",
		series: "系列"
	}[e] || "资料"), a ? "添加关注来源并获取内容后，这里会显示对应标签。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: a ? s : o + s });
}
//#endregion
//#region src/sidebar.ts
function Ln(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Rn(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function zn(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function Bn(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function Vn(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function Hn() {
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupgrid">${[
		[
			"扫描与采集",
			"扫描并补全资料",
			"扫描媒体文件夹，导入已有资料，采集缺失信息。"
		],
		[
			"垃圾文件",
			"查看垃圾文件",
			""
		],
		[
			"重复文件",
			"查看重复文件",
			""
		],
		[
			"空文件夹",
			"删除空文件夹",
			""
		],
		[
			"人工复核",
			"查看候选",
			""
		],
		[
			"回收站",
			"查看回收站",
			""
		],
		[
			"高清版",
			"查看高清版",
			""
		]
	].map(([e, t, n], r) => `
      <section class="cleanupfieldset" data-geist-fieldset aria-labelledby="cleanup-loading-${r}">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-${r}">${e}</h3>
          ${n ? `<p>${n}</p>` : "<strong><span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span></strong>"}
          ${r === 3 ? "<p class=\"cleanupmeta\"><span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span></p>" : ""}</div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button"${r === 3 ? " class=\"danger\"" : ""} disabled>${r === 3 ? "<svg aria-hidden=\"true\"><use href=\"#i-trash\"></use></svg><span>" + t + "</span>" : t}</button></footer>
      </section>`).join("")}</div></div>`;
}
function Un(e, t = !1, n = !1) {
	if (t || n) return "";
	let r = "<svg aria-hidden=\"true\"><use href=\"#i-external-link\"></use></svg>";
	return `<details class="taste-history-guide"${e ? " open" : ""}>
    <summary>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${r}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${r}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      <button type="button" class="geist-button taste-guide-skip">跳过</button>
    </div></details>`;
}
var Wn = "peach-taste-guide-dismissed";
function Gn(e, t) {
	d(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Wn, "1"), n.remove();
	});
}
//#endregion
//#region src/jav-artwork.ts
function Kn(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function qn(e) {
	return {
		javLayout: Kn(e.javLayout),
		javImage: Jn(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Jn(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Yn(e, t) {
	return e.is_jav && e.code && e.has_cover && (Jn(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Xn(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Jn(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var Zn = {
	"library-processing": {
		load: mn,
		component: hn
	},
	scraping: {
		load: un,
		component: pn
	},
	"quality-goals": {
		load: an,
		component: sn
	},
	configuration: {
		load: ut,
		component: gt
	}
}, Qn = () => Object.keys(Zn), $n = /* @__PURE__ */ new Map();
async function er(e, t, n, r = {}) {
	let i = Zn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	tr(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	$n.set(t, a);
	let o;
	try {
		o = {
			data: await i.load(n, a.controller.signal),
			error: ""
		};
	} catch (e) {
		if (a.controller.signal.aborted) return;
		o = {
			data: null,
			error: R(e)
		};
	}
	if ($n.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		$n.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	Ee(ie(i.component, s), t);
}
function tr(e) {
	let t = $n.get(e);
	t && (t.controller.abort(), $n.delete(e), t.painted && Ee(null, e));
}
//#endregion
export { Wn as TASTE_GUIDE_KEY, In as catalogEmptyHtml, Fn as catalogSuggestions, Hn as cleanupSkeletonHtml, Bn as cloudLocations, Vn as cloudPreferenceLocations, Cn as createReviewSelection, Pn as emptyCatalogLayout, Mn as entitySkeletonHtml, ln as followJobProgress, xn as identityEvidenceHtml, Qn as islandNames, Yn as javImageKind, An as matchesFaceSource, er as mountIsland, jn as nativeImageFit, Jn as normalizeJavImage, Kn as normalizeJavLayout, qn as normalizeJavPreferences, De as preferredDirection, vn as refreshStore, bn as reviewImageHtml, Ln as sidebarHasCatalogContent, zn as sidebarTagCounts, _n as storeNames, Xn as syncJavImages, Rn as syncSidebarSurface, Un as tasteHistoryGuideHtml, tr as unmountIsland, cn as watchJob, Sn as wireReviewPictures, kn as wireReviewSelection, Gn as wireTasteHistoryGuide };
