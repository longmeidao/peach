import { LOC as e, esc as t, fmtDur as n, fmtSize as r, icon as i, requestErrorMessage as a } from "/js/core.js";
import { MEDIA_SOURCE_ICONS as o, checkboxHtml as s, confirmModal as c, emptyStateHtml as l, fieldsetTitle as u, loadingDotsHtml as d, noteHtml as f, progressHtml as p, projectBannerHtml as m, selectFieldHtml as h, selectOptionIconHtml as g, setActionBusy as _, wireCollapse as v, wireSelectField as y } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var b, x, S, C, w, T, E, D, O, k, A, ee, j, M, N, P = {}, te = [], ne = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, re = Array.isArray;
function F(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ie(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function ae(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? b.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return oe(e, o, r, i, null);
}
function oe(e, t, n, r, i) {
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
		__v: i ?? ++S,
		__i: -1,
		__u: 0
	};
	return i == null && x.vnode != null && x.vnode(a), a;
}
function I(e) {
	return e.children;
}
function se(e, t) {
	this.props = e, this.context = t;
}
function L(e, t) {
	if (t == null) return e.__ ? L(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? L(e) : null;
}
function ce(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = F({}, t);
		a.__v = t.__v + 1, x.vnode && x.vnode(a), ye(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? L(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, xe(r, a, i), t.__e = t.__ = null, a.__e != n && le(a);
	}
}
function le(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), le(e);
}
function ue(e) {
	(!e.__d && (e.__d = !0) && w.push(e) && !de.__r++ || T != x.debounceRendering) && ((T = x.debounceRendering) || E)(de);
}
function de() {
	try {
		for (var e, t = 1; w.length;) w.length > t && w.sort(D), e = w.shift(), t = w.length, ce(e);
	} finally {
		w.length = de.__r = 0;
	}
}
function fe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || te, v = t.length;
	for (c = pe(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || P, p.__i = d, g = ye(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && we(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = me(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function pe(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = oe(null, o, null, null, null) : re(o) ? o = e.__k[a] = oe(I, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = oe(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = he(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = L(s)), Te(s, s));
	return r;
}
function me(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = me(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = L(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function he(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function ge(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || ne.test(t) ? n : n + "px";
}
function _e(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ge(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ge(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(ee, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[A] = r[A] : (n[A] = j, e.addEventListener(t, a ? N : M, a)) : e.removeEventListener(t, a ? N : M, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ve(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[k] == null) t[k] = j++;
			else if (t[k] < n[A]) return;
			return n(x.event ? x.event(t) : t);
		}
	};
}
function ye(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, y, b, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = x.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, y = D.prototype && D.prototype.render, b = (u = D.contextType) && r[u.__c], S = u ? b ? b.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (y ? t.__c = f = new D(v, S) : (t.__c = f = new se(v, S), f.constructor = D, f.render = Ee), b && b.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), y && f.__s == null && (f.__s = f.state), y && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = F({}, f.__s)), F(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) y && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), y && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (y && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, S)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), te.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = L(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, S), y && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = S, f.props = v, f.__P = e, f.__e = !1, C = x.__r, w = 0, y) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), te.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = F(F({}, r), f.getChildContext())), y && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === I && u.key == null ? Se(u.props.children) : u, s = fe(e, re(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ie(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || be(t), x.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = Ce(n.__e, t, n, r, i, a, o, c, l);
	return (u = x.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function be(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(be));
}
function xe(e, t, n) {
	for (var r = 0; r < n.length; r++) we(n[r], n[++r], n[++r]);
	x.__c && x.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			x.__e(e, t.__v);
		}
	});
}
function Se(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : re(e) ? e.map(Se) : e.constructor === void 0 ? F({}, e) : null;
}
function Ce(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || P, _ = t.props, v = t.type;
	if (v == "svg" ? i = "http://www.w3.org/2000/svg" : v == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!v && (v ? p.localName == v : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (v == null) return document.createTextNode(_);
		e = document.createElementNS(i, v, _.is && _), s &&= (x.__m && x.__m(t, a), !1), a = null;
	}
	if (v == null) g === _ || s && e.data == _ || (e.data = _);
	else {
		if (a = v == "textarea" && _.defaultValue != null ? null : a && b.call(e.childNodes), !s && a != null) for (g = {}, l = 0; l < e.attributes.length; l++) g[(p = e.attributes[l]).name] = p.value;
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || _e(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || _e(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), fe(t.type == "template" ? e.content : e, re(f) ? f : [f], t, n, r, v == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && L(n, 0), s, c), a != null) for (l = a.length; l--;) ie(a[l]);
		s && v != "textarea" || (l = "value", v == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || v == "progress" && !m || v == "option" && m != g[l]) && _e(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && _e(e, l, h, g[l], i));
	}
	return e;
}
function we(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		x.__e(e, n);
	}
}
function Te(e, t, n) {
	var r, i;
	if (x.unmount && x.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || we(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			x.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && Te(r[i], t, n || typeof e.type != "function");
	n || ie(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Ee(e, t, n) {
	return this.constructor(e, n);
}
function De(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), x.__ && x.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], ye(t, e = (!r && n || t).__k = ae(I, null, [e]), i || P, P, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? b.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), xe(a, e, o), e.props.children = null;
}
b = te.slice, x = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, S = 0, C = function(e) {
	return e != null && e.constructor === void 0;
}, se.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = F({}, this.state);
	typeof e == "function" && (e = e(F({}, n), this.props)), e && F(n, e), e != null && this.__v && (t && this._sb.push(t), ue(this));
}, se.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ue(this));
}, se.prototype.render = I, w = [], E = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, D = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, de.__r = 0, O = Math.random().toString(8), k = "__d" + O, A = "__a" + O, ee = /(PointerCapture)$|Capture$/i, j = 0, M = ve(!1), N = ve(!0);
//#endregion
//#region src/sort-preferences.ts
function Oe(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/api.ts
var ke = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(a(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Ae = (e) => {
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
}, R = (e) => a(e);
async function z(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new ke(Ae(r) || `请求失败（${n.status}）`, n.status);
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
	if (!i.ok) throw new ke(Ae(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var V, H, je, Me, Ne = 0, Pe = [], U = x, Fe = U.__b, Ie = U.__r, Le = U.diffed, Re = U.__c, ze = U.unmount, Be = U.__;
function Ve(e, t) {
	U.__h && U.__h(H, e, Ne || t), Ne = 0;
	var n = H.__H || (H.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function W(e) {
	return Ne = 1, He(Xe, e);
}
function He(e, t, n) {
	var r = Ve(V++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Xe(void 0, t), function(e) {
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
	var n = Ve(V++, 3);
	!U.__s && Ye(n.__H, t) && (n.__ = e, n.u = t, H.__H.__h.push(n));
}
function K(e, t) {
	var n = Ve(V++, 4);
	!U.__s && Ye(n.__H, t) && (n.__ = e, n.u = t, H.__h.push(n));
}
function q(e) {
	return Ne = 5, Ue(function() {
		return { current: e };
	}, []);
}
function Ue(e, t) {
	var n = Ve(V++, 7);
	return Ye(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function We() {
	for (var e; e = Pe.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(qe), t.__h.some(Je), t.__h = [];
		} catch (n) {
			t.__h = [], U.__e(n, e.__v);
		}
	}
}
U.__b = function(e) {
	H = null, Fe && Fe(e);
}, U.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Be && Be(e, t);
}, U.__r = function(e) {
	Ie && Ie(e), V = 0;
	var t = (H = e.__c).__H;
	t && (je === H ? (t.__h = [], H.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(qe), t.__h.some(Je), t.__h = [], V = 0)), je = H;
}, U.diffed = function(e) {
	Le && Le(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Pe.push(t) !== 1 && Me === U.requestAnimationFrame || ((Me = U.requestAnimationFrame) || Ke)(We)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), je = H = null;
}, U.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(qe), e.__h = e.__h.filter(function(e) {
				return !e.__ || Je(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], U.__e(n, e.__v);
		}
	}), Re && Re(e, t);
}, U.unmount = function(e) {
	ze && ze(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			qe(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && U.__e(t, n.__v));
};
var Ge = typeof requestAnimationFrame == "function";
function Ke(e) {
	var t, n = function() {
		clearTimeout(r), Ge && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Ge && (t = requestAnimationFrame(n));
}
function qe(e) {
	var t = H, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), H = t;
}
function Je(e) {
	var t = H;
	e.__c = e.__(), H = t;
}
function Ye(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function Xe(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var Ze = 0;
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
		__v: --Ze,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return x.vnode && x.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function Qe({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1, disabled: s = !1 }) {
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
function $e({ initial: e, receipt: t }) {
	let [n, r] = W(e), [i, a] = W(""), [o, s] = W(""), [c, l] = W(""), [d, p] = W(!1), [m, h] = W(""), [g, v] = W({}), y = q(null), b = q(!1), x = q(null);
	return /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-fieldset-type": d ? "warning" : void 0,
		onSubmit: async (e) => {
			if (e.preventDefault(), b.current) return;
			h("");
			let u = {};
			if (n.mode === "password" && !i && (u.current_password = "请输入当前访问密码"), d || ((o.length < 8 || o.length > 256) && (u.password = "访问密码需为 8–256 个字符"), o !== c && (u.confirmation = "两次输入的密码不一致")), v(u), Object.keys(u).length) {
				requestAnimationFrame(() => y.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			b.current = !0, _(x.current, !0);
			try {
				let e = await B("/api/configuration/access", {
					revision: n.revision,
					action: d ? "disable" : "set",
					confirm_disable: d,
					current_password: i,
					password: d ? "" : o,
					confirmation: d ? "" : c
				});
				r(e), a(""), s(""), l(""), p(!1), v({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof ke ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? v(n) : h(R(e));
			} finally {
				b.current = !1, _(x.current, !1);
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
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("accessTitle", "访问密码") } }), /* @__PURE__ */ J("p", {
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
							checked: d,
							onChange: (e) => p(e.currentTarget.checked)
						}), /* @__PURE__ */ J("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ J("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ J("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				n.mode === "password" ? /* @__PURE__ */ J(Qe, {
					id: "access-current",
					label: "当前访问密码",
					value: i,
					onInput: a,
					error: g.current_password,
					current: !0
				}) : null,
				n.mode === "locked" ? null : /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J(Qe, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: o,
					onInput: s,
					disabled: d,
					error: d ? void 0 : g.password,
					help: d ? "关闭访问密码时无需填写。" : "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ J(Qe, {
					id: "access-confirm",
					label: "确认访问密码",
					value: c,
					onInput: l,
					disabled: d,
					error: d ? void 0 : g.confirmation
				})] }),
				d && /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: f("保存后，能连接到 Peach 的设备将直接访问馆藏。", {
					variant: "warning",
					label: "访问范围"
				}) } }),
				m ? /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: m
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
var et = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function tt({ initial: e, initialJob: t }) {
	let [n, r] = W(e), [i, a] = W(t || {
		state: "idle",
		progress: 0
	}), [o, s] = W(""), l = q(null), d = q(!0), m = q(!1), h = q(null);
	G(() => {
		_(h.current, et.has(i.state));
	}, [i.state]), G(() => () => {
		d.current = !1, l.current?.abort();
	}, []);
	let g = async () => {
		let e = await B("/api/configuration/update-restart", {});
		d.current && a(e);
	};
	G(() => {
		i.state !== "ready" || m.current || (m.current = !0, c({
			title: "更新已准备好",
			body: `Peach ${i.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: g
		}));
	}, [i.state]), G(() => {
		if (!et.has(i.state)) return;
		let e = new AbortController(), t, n = 0, o = async () => {
			try {
				let t = await z("/api/configuration/update-status", e.signal);
				e.signal.aborted || (a(t), n = 0, t.state === "complete" && r((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				})));
			} catch {
				++n >= 120 && !e.signal.aborted && s("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && n < 120 && (t = setTimeout(o, 1e3));
		};
		return t = setTimeout(o, 1e3), () => {
			e.abort(), clearTimeout(t);
		};
	}, [i.state]);
	let v = async (e) => {
		if (l.current || et.has(i.state)) return;
		let t = new AbortController();
		l.current = t, m.current = !1, s(""), _(e, !0);
		try {
			let e = await B("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || a(e);
		} catch (e) {
			t.signal.aborted || s(R(e));
		} finally {
			l.current = null, _(e, !1);
		}
	}, y = async (t) => {
		if (l.current) return;
		let n = new AbortController();
		l.current = n, _(t, !0), s("");
		try {
			let e = await z("/api/configuration/updates", n.signal);
			n.signal.aborted || r(e);
		} catch (t) {
			n.signal.aborted || (r({
				...e,
				state: "error"
			}), s(R(t)));
		} finally {
			l.current = null, _(t, !1);
		}
	};
	return /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ J("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ J("dt", { children: "当前版本" }),
						/* @__PURE__ */ J("dd", { children: n.current_version }),
						/* @__PURE__ */ J("dt", { children: "安装方式" }),
						/* @__PURE__ */ J("dd", { children: n.installation }),
						/* @__PURE__ */ J("dt", { children: "更新通道" }),
						/* @__PURE__ */ J("dd", { children: n.channel }),
						/* @__PURE__ */ J("dt", { children: "最新版本" }),
						/* @__PURE__ */ J("dd", { children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				n.state === "available" && !o ? /* @__PURE__ */ J("div", {
					role: "status",
					dangerouslySetInnerHTML: { __html: f(n.message, { label: "有可用更新" }) }
				}) : /* @__PURE__ */ J("p", {
					class: o || n.state === "error" ? "configbad" : "confighelp",
					role: o || n.state === "error" ? "alert" : "status",
					children: o || n.message
				}),
				i.state === "idle" ? null : /* @__PURE__ */ J("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ J("p", {
						class: i.state === "error" ? "configbad" : "confighelp",
						children: i.message
					}), i.state === "error" ? null : /* @__PURE__ */ J(I, { children: [
						/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: p("更新准备进度：下载、校验、解压、准备安装", i.progress, 100, { stops: [
							{
								value: 65,
								label: "下载结束"
							},
							{
								value: 67,
								label: "校验结束"
							},
							{
								value: 90,
								label: "准备安装"
							}
						] }) } }),
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: ["下载 → 校验 → 解压 → 准备安装 · ", i.message]
						}),
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: i.state === "downloading" && i.total ? `${((i.downloaded || 0) / 1048576).toFixed(1)} / ${(i.total / 1048576).toFixed(1)} MB` : `${i.progress}%`
						})
					] })]
				})
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ J("a", {
					class: "geist-button",
					href: n.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: "查看发布页"
				}),
				i.state === "ready" ? /* @__PURE__ */ J("button", {
					type: "button",
					class: "geist-button primary",
					onClick: () => {
						c({
							title: "更新已准备好",
							body: `Peach ${i.version || ""} 将在重启后安装。`,
							confirmLabel: "立即重启",
							cancelLabel: "稍后",
							onConfirm: g
						});
					},
					children: "重启安装"
				}) : null,
				n.state === "available" && n.installation === "独立测试包" && i.state !== "ready" ? /* @__PURE__ */ J("button", {
					ref: h,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => v(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ J("button", {
					type: "button",
					class: "geist-button",
					disabled: et.has(i.state),
					onClick: (e) => y(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function nt({ initial: e, receipt: t }) {
	let [n, r] = W(e), [i, a] = W(e.mode), [o, s] = W(""), [c, l] = W(""), d = q(!1), f = q(null), p = q(null), m = q(new AbortController());
	G(() => () => m.current.abort(), []), K(() => {
		let t = f.current;
		t.innerHTML = h([
			["environment", "系统代理"],
			["direct", "直连"],
			["proxy", "自定义"]
		], e.mode, {
			label: "Peach 代理",
			className: "configselect",
			attr: "data-fixed-width"
		});
		let n = y(t.firstElementChild), r = () => a(n.value);
		return n.addEventListener("change", r), () => {
			n.removeEventListener("change", r), t.replaceChildren();
		};
	}, []);
	async function g() {
		if (!d.current) {
			d.current = !0, _(p.current, !0), l("");
			try {
				let e = await B("/api/configuration/peach-proxy", {
					mode: i,
					proxy: o
				}, "POST", m.current.signal);
				m.current.signal.aborted || (r(e), s(""), t("已保存 Peach 代理"));
			} catch (e) {
				m.current.signal.aborted || l(R(e));
			} finally {
				d.current = !1, _(p.current, !1);
			}
		}
	}
	return /* @__PURE__ */ J("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), g();
		},
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("peachProxyTitle", "Peach 代理") } }), /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: "采集来源选择“Peach 代理”时共用此设置。"
					})]
				}),
				/* @__PURE__ */ J("div", { ref: f }),
				i === "proxy" && /* @__PURE__ */ J("div", {
					class: "configfield",
					children: [/* @__PURE__ */ J("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ J("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: o,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => s(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ J("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				c && /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: c
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				ref: p,
				class: "geist-button primary",
				type: "submit",
				children: "保存代理"
			})
		})]
	});
}
//#endregion
//#region src/islands/desktop-settings.tsx
function rt({ label: e, checked: t, disabled: n, change: r }) {
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
function it({ label: e, checked: t, disabled: n, change: r }) {
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
function at({ startup: e, receipt: t }) {
	let [n, r] = W(e.enabled), [i, a] = W(e.silent), [o, s] = W(""), c = q(!1), l = q(null);
	async function d() {
		if (!c.current) {
			c.current = !0, _(l.current, !0), s("");
			try {
				await B("/api/configuration/startup", {
					enabled: n,
					silent: i
				}), t("已保存开机自启");
			} catch (e) {
				s(R(e));
			} finally {
				c.current = !1, _(l.current, !1);
			}
		}
	}
	return /* @__PURE__ */ J("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), d();
		},
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("startupTitle", "开机自启") } }),
				/* @__PURE__ */ J("div", {
					class: "configoptions",
					role: "group",
					"aria-labelledby": "startupTitle",
					children: [/* @__PURE__ */ J(it, {
						label: "开机后启动 Peach",
						checked: n,
						disabled: !e.available,
						change: r
					}), /* @__PURE__ */ J("div", {
						class: "configoption",
						children: [/* @__PURE__ */ J(it, {
							label: "静默启动",
							checked: i,
							disabled: !e.available,
							change: a
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
				o && /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: o
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				ref: l,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存配置"
			})
		})]
	});
}
function ot({ data: e }) {
	let t = q(null);
	return K(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let a = document.createElement("summary");
		a.innerHTML = i("chevron-right") + "<span>数据目录</span>", r.append(a);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), v(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ J("div", { ref: t });
}
function st({ uninstall: e }) {
	let [t, n] = W(!1), [r, i] = W("");
	async function a() {
		await c({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序和开机自启。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await B("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				i(e.message);
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
					children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("uninstallTitle", "卸载 Peach") } }), e.available && /* @__PURE__ */ J("p", {
						class: "confighelp",
						children: "卸载会退出 Peach、移除程序和开机自启。原始媒体文件保留。"
					})]
				}),
				/* @__PURE__ */ J(rt, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!r,
					change: n
				}),
				/* @__PURE__ */ J(ot, { data: e }),
				e.message && /* @__PURE__ */ J("p", {
					class: "confighelp",
					children: e.message
				}),
				r && /* @__PURE__ */ J("p", {
					class: "confighelp",
					role: "status",
					children: r
				})
			]
		}), /* @__PURE__ */ J("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				type: "button",
				class: "geist-button danger",
				disabled: !e.available || !!r,
				onClick: () => void a(),
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/islands/clouddrive-guide.tsx
var ct = [
	{
		name: "机械硬盘或内存不超过 8 GB",
		cache: "10–20 GiB",
		read: "256 / 128 KB",
		task: "同时处理 1 个视频",
		advice: "缓存优先放内置 SSD。只有机械硬盘时，先用按需读取；反复观看同一批文件才开启文件夹缓存。"
	},
	{
		name: "SATA SSD，8–16 GB 内存",
		cache: "20–50 GiB",
		read: "256 / 128 KB",
		task: "同时处理 1–2 个视频",
		advice: "扫描、抽帧用小读块。观看高码率视频若仍缓冲，再试 512 / 256 KB。"
	},
	{
		name: "NVMe SSD，16 GB 以上内存",
		cache: "50–100 GiB",
		read: "256 / 128 KB",
		task: "同时处理 2 个视频起步",
		advice: "以扫描和拖动播放为主时保留小读块。连续看高码率视频可试 512 / 256 KB，速度不升就调回。"
	}
];
function lt() {
	let e = q(null);
	return K(() => {
		e.current && v(e.current, "details", "clouddrive-guide");
	}, []), /* @__PURE__ */ J("div", {
		ref: e,
		class: "cloudguide",
		children: [/* @__PURE__ */ J("p", {
			class: "confighelp",
			children: ["先在 CloudDrive 登录网盘并挂载，开启「启动时自动挂载」。", /* @__PURE__ */ J("a", {
				href: "https://www.clouddrive2.com/help.html",
				target: "_blank",
				rel: "noreferrer",
				children: ["挂载帮助", /* @__PURE__ */ J("svg", {
					"aria-hidden": "true",
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
				})]
			})]
		}), /* @__PURE__ */ J("details", { children: [
			/* @__PURE__ */ J("summary", { children: "CloudDrive 速度与缓存建议" }),
			/* @__PURE__ */ J("p", {
				class: "confighelp",
				children: "按缓存所在的硬盘选起步配置。优先保证播放流畅，再用同一视频比较冷启动、拖动和流量；参数越大不一定越快。"
			}),
			/* @__PURE__ */ J("div", {
				class: "cloudguide-profiles",
				children: ct.map((e) => /* @__PURE__ */ J("section", {
					"aria-label": e.name,
					children: [
						/* @__PURE__ */ J("h4", { children: e.name }),
						/* @__PURE__ */ J("dl", { children: [
							/* @__PURE__ */ J("dt", { children: "磁盘缓存上限" }),
							/* @__PURE__ */ J("dd", { children: e.cache }),
							/* @__PURE__ */ J("dt", { children: "默认 / 最小读取长度" }),
							/* @__PURE__ */ J("dd", { children: e.read }),
							/* @__PURE__ */ J("dt", { children: "Peach 并行任务" }),
							/* @__PURE__ */ J("dd", { children: e.task })
						] }),
						/* @__PURE__ */ J("p", {
							class: "confighelp",
							children: e.advice
						})
					]
				}, e.name))
			}),
			/* @__PURE__ */ J("ul", {
				class: "cloudguide-notes",
				children: [
					/* @__PURE__ */ J("li", { children: "在 CloudDrive「设置」中设置磁盘缓存上限和 LRU（优先清理最久没用的缓存）。系统盘至少留 40 GiB；上限不要填 0。设置后重新打开确认，并观察实际占盘。" }),
					/* @__PURE__ */ J("li", { children: "在各网盘的下载设置中调整读取长度和下载线程。115 从 2 线程开始，遵守当前客户端上限；PikPak / WebDAV 从 2 线程开始，带宽充足且速度确实提升时再试 4。开启支持的直链选项，确认播放可用。" }),
					/* @__PURE__ */ J("li", { children: "PikPak 按当前 CloudDrive 提供的接入方式配置；使用 WebDAV 时，先确认服务端允许直链。不能直接套用 115 的连接方式。" }),
					/* @__PURE__ */ J("li", { children: "看视频时暂停批量抽帧，关闭不用的播放页。下载速度应高于视频码率除以 8，并留出余量：80 Mbps 视频约需 10 MB/s，建议稳定达到 15 MB/s。" }),
					/* @__PURE__ */ J("li", { children: "Buffer Cache 的内存占用、磁盘缓存和文件夹缓存是不同设置。磁盘显示的逻辑大小也不等于实际占盘；只改一个上限不能限制所有缓存。" })
				]
			}),
			/* @__PURE__ */ J("p", {
				class: "confighelp",
				children: ["上表容量和并发是起步建议，按实际占盘与播放结果调整。直链和代理是不同设置；连接慢时分别比较，不能只看开关是否开启。", /* @__PURE__ */ J("a", {
					href: "https://www.clouddrive2.com/features.html",
					target: "_blank",
					rel: "noreferrer",
					children: ["缓存说明", /* @__PURE__ */ J("svg", {
						"aria-hidden": "true",
						viewBox: "0 0 24 24",
						children: /* @__PURE__ */ J("use", { href: "#i-external-link" })
					})]
				})]
			})
		] })]
	});
}
//#endregion
//#region src/islands/configuration.tsx
var ut = "/api/configuration", dt = "/api/pick-folder", ft = 8e3, pt = (e, t) => z(ut, t), mt = ({ html: e, class: t }) => /* @__PURE__ */ J("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), ht = (e) => !(e instanceof ke) || e.status !== 400 ? null : e.body?.errors ?? null;
function gt({ facts: e }) {
	return /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ J(mt, { html: u("configFactsTitle", "运行信息") }), /* @__PURE__ */ J("dl", {
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
function _t({ data: e }) {
	let [t, n] = W(e.media_sources), [r, i] = W(""), a = q(null);
	G(() => () => a.current?.abort(), []);
	let s = async (e) => {
		if (a.current) return;
		let t = new AbortController();
		a.current = t, _(e, !0), i("");
		try {
			let e = await z(ut, t.signal);
			t.signal.aborted || n(e.media_sources);
		} catch (e) {
			t.signal.aborted || i(R(e));
		} finally {
			a.current = null, _(e, !1);
		}
	};
	return t ? /* @__PURE__ */ J("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J(mt, { html: u("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ J("dl", {
					class: "configfacts",
					children: t.map((e) => /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("dt", { children: [/* @__PURE__ */ J("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: g(o[e.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[e.location] || e.location] }), /* @__PURE__ */ J("dd", { children: [
						e.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ J("span", {
							class: `configstatus ${e.online === !0 ? "online" : e.online === !1 ? "offline" : "unknown"}`,
							children: e.online === !0 ? "在线" : e.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				r ? /* @__PURE__ */ J("p", {
					class: "configbad",
					role: "alert",
					children: r
				}) : null
			]
		}), /* @__PURE__ */ J("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ J("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => s(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function vt({ value: e, label: t, onChange: n }) {
	let r = q(null), i = q(null), a = q(n);
	return a.current = n, K(() => {
		let n = r.current;
		n.innerHTML = h([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([e, t]) => [
			e,
			t,
			o[e]
		]), e, { label: t });
		let s = y(n.firstElementChild);
		i.current = s;
		let c = () => a.current(s.value);
		return s.addEventListener("change", c), () => {
			i.current = null, s.disabled = !0, s.removeEventListener("change", c), n.replaceChildren();
		};
	}, [t]), K(() => {
		i.current && (i.current.value = e);
	}, [e]), /* @__PURE__ */ J("div", {
		ref: r,
		class: "configsourcecontrol"
	});
}
function yt({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, i] = W(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [a, o] = W(n?.map((e) => e.location) ?? []), [s, c] = W(n?.map((e) => e.root) ?? []), [l, d] = W(String(e.port)), [p, m] = W(!1), [h, g] = W([]), [v, y] = W(""), [b, x] = W(""), [S, C] = W(null), [w, T] = W(null), E = q(!1), D = q(e.revision), O = q([]), k = q(null);
	K(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), G(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), ft);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		i((n) => n.map((n, r) => r === e ? t : n));
	}, ee = () => {
		T(r.length), i((e) => [...e, ""]);
	}, j = (e) => {
		o((t) => t.filter((t, n) => n !== e)), c((t) => t.filter((t, n) => n !== e)), i((t) => t.filter((t, n) => n !== e)), g((t) => t.filter((t, n) => n !== e));
	}, M = (e, t) => {
		g((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, N = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			_(t, !0);
			try {
				let { path: t } = await B(dt, { initial: r[e] ?? "" });
				t && (A(e, t), M(e, ""));
			} catch (t) {
				M(e, R(t));
			} finally {
				_(t, !1);
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
				E.current = !0, _(k.current, !0), x("");
				try {
					let n = await B(ut, {
						revision: D.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: a[t] || "local",
							root: s[t] || ""
						})) } : {},
						port: l,
						scan_now: p
					});
					D.current = n.revision, g([]), y(""), t("已保存配置"), C(n);
				} catch (e) {
					let t = ht(e);
					t ? (g(t.media_dirs ?? []), y(t.port ?? "")) : (g([]), y(""), x(R(e)));
				} finally {
					E.current = !1, _(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ J("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ J(mt, { html: u("configTitle", "这台电脑") }),
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
										"aria-invalid": h[n] ? "true" : void 0,
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
											children: ["媒体来源", /* @__PURE__ */ J(vt, {
												label: `媒体来源 ${n + 1}`,
												value: a[n] || "local",
												onChange: (e) => {
													let t = [...a];
													t[n] = e, o(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ J("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ J("input", {
											class: "geist-input",
											"aria-label": `Windows 中的对应路径 ${n + 1}`,
											value: s[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...s];
												t[n] = e.currentTarget.value, c(t);
											}
										})] }) : null]
									}),
									h[n] ? /* @__PURE__ */ J("p", {
										class: "configbad",
										role: "alert",
										children: h[n]
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
						a.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ J(lt, {}) : null,
						a.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ J("p", {
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
							value: l,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => d(e.currentTarget.value)
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
							checked: p,
							onChange: (e) => m(e.currentTarget.checked)
						}), /* @__PURE__ */ J("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ J("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ J("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ J("span", { children: "保存后扫描并补全资料" })]
				}),
				b ? /* @__PURE__ */ J(mt, { html: f(b, {
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
function bt({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ J(mt, {
		class: "configpage",
		html: f(n || "没有读到配置", {
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
			t.startup ? /* @__PURE__ */ J(at, {
				startup: t.startup,
				receipt: e
			}) : null,
			/* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			t.editable ? /* @__PURE__ */ J(yt, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ J(mt, { html: f(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ J(_t, { data: t }),
			t.peach_proxy || t.access ? /* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy ? /* @__PURE__ */ J(nt, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ J($e, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ J("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			t.updates ? /* @__PURE__ */ J(tt, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ J(gt, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ J(st, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var xt = Symbol.for("preact-signals");
function St() {
	if (X > 1) X--;
	else {
		var e, t = !1;
		for ((function() {
			var e = At;
			for (At = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); Et !== void 0;) {
			var n = Et;
			for (Et = void 0, Dt++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && Pt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (Dt = 0, X--, t) throw e;
	}
}
function Ct(e) {
	if (X > 0) return e();
	kt = ++Ot, X++;
	try {
		return e();
	} finally {
		St();
	}
}
var wt, Y = void 0;
function Tt(e) {
	var t = Y, n = wt;
	Y = void 0, wt = void 0;
	try {
		return e();
	} finally {
		Y = t, wt = n;
	}
}
var Et = void 0, X = 0, Dt = 0, Ot = 0, kt = 0, At = void 0, jt = 0;
function Mt(e) {
	if (Y !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== Y) return t = {
			i: 0,
			S: e,
			p: Y.s,
			n: void 0,
			t: Y,
			e: void 0,
			x: void 0,
			r: t
		}, Y.s !== void 0 && (Y.s.n = t), Y.s = t, e.n = t, 32 & Y.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = Y.s, t.n = void 0, Y.s.n = t, Y.s = t), t;
	}
}
function Z(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Z.prototype.brand = xt, Z.prototype.h = function() {
	return !0;
}, Z.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? Tt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Z.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && Tt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Z.prototype.subscribe = function(e) {
	var t = this;
	return Ht(function() {
		var n = t.value;
		Tt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Z.prototype.valueOf = function() {
	return this.value;
}, Z.prototype.toString = function() {
	return this.value + "";
}, Z.prototype.toJSON = function() {
	return this.value;
}, Z.prototype.peek = function() {
	var e = this;
	return Tt(function() {
		return e.value;
	});
}, Object.defineProperty(Z.prototype, "value", {
	get: function() {
		var e = Mt(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (Dt > 100) throw Error("Cycle detected");
			(function(e) {
				X !== 0 && Dt === 0 && e.l !== kt && (e.l = kt, At = {
					S: e,
					v: e.v,
					i: e.i,
					o: At
				});
			})(this), this.v = e, this.i++, jt++, X++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				St();
			}
		}
	}
});
function Nt(e, t) {
	return new Z(e, t);
}
function Pt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Ft(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function It(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function Q(e, t) {
	Z.call(this, void 0, t), this.x = e, this.s = void 0, this.g = jt - 1, this.f = 4;
}
Q.prototype = new Z(), Q.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === jt)) return !0;
	if (this.g = jt, this.f |= 1, this.i > 0 && !Pt(this)) return this.f &= -2, !0;
	var e = Y;
	try {
		Ft(this), Y = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return Y = e, It(this), this.f &= -2, !0;
}, Q.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Z.prototype.S.call(this, e);
}, Q.prototype.U = function(e) {
	if (this.t !== void 0 && (Z.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, Q.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(Q.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = Mt(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function Lt(e, t) {
	return new Q(e, t);
}
function Rt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		X++;
		var n = Y;
		Y = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, zt(e), t;
		} finally {
			Y = n, St();
		}
	}
}
function zt(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Rt(e);
}
function Bt(e) {
	if (Y !== this) throw Error("Out-of-order effect");
	It(this), Y = e, this.f &= -2, 8 & this.f && zt(this), St();
}
function Vt(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, wt && wt.push(this);
}
Vt.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Vt.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Rt(this), Ft(this), X++;
	var e = Y;
	return Y = this, Bt.bind(this, e);
}, Vt.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = Et, Et = this);
}, Vt.prototype.d = function() {
	this.f |= 8, 1 & this.f || zt(this);
}, Vt.prototype.dispose = function() {
	this.d();
};
function Ht(e, t) {
	var n = new Vt(e, t);
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
var Ut, Wt, Gt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Kt = [];
Ht(function() {
	Ut = this.N;
})();
function qt(e, t) {
	x[e] = t.bind(null, x[e] || function() {});
}
function Jt(e) {
	if (Wt) {
		var t = Wt;
		Wt = void 0, t();
	}
	Wt = e && e.S();
}
function Yt(e) {
	var t = this, n = e.data, r = Zt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Ue(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = Lt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = Lt(function() {
			return !Array.isArray(i.value) && !C(i.value);
		}), o = Ht(function() {
			if (this.N = en, a.value) {
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
Yt.displayName = "ReactiveTextNode", Object.defineProperties(Z.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Yt
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
}), qt("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Z && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), qt("__r", function(e, t) {
	if (e(t), t.type !== I) {
		Jt();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Ht(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				Gt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Jt(n);
	}
}), qt("__e", function(e, t, n, r) {
	Jt(), e(t, n, r);
}), qt("diffed", function(e, t) {
	Jt();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Xt(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Xt(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = Nt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Ht(function() {
			this.N = en;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
qt("unmount", function(e, t) {
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
}), qt("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), se.prototype.shouldComponentUpdate = function(e, t) {
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
function Zt(e, t) {
	return Ue(function() {
		return Nt(e, t);
	}, []);
}
var Qt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function $t() {
	Ct(function() {
		for (var e; e = Kt.shift();) Ut.call(e);
	});
}
function en() {
	Kt.push(this) === 1 && (x.requestAnimationFrame || Qt)($t);
}
//#endregion
//#region src/state/quality-goals.ts
var tn = "/api/quality-goals?limit=200", nn = {
	data: null,
	error: ""
}, rn = Nt(nn), an = 0, on = Lt(() => rn.value);
Lt(() => rn.value.data?.total ?? null);
function sn() {
	an += 1, rn.value = nn;
}
async function cn(e) {
	let t = an += 1;
	try {
		let n = await z(tn, e);
		return t === an && (rn.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === an && (rn.value = {
			data: null,
			error: R(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var ln = (e, t) => cn(t), un = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function dn({ openItem: t, javTitleHtml: i, javDisplayName: a, srcBadge: o }) {
	let { data: s, error: c } = on.value;
	if (c) return /* @__PURE__ */ J("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: f(c, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let u = s?.items ?? [];
	return u.length ? /* @__PURE__ */ J("div", {
		class: "qualitylist",
		children: u.map((s) => /* @__PURE__ */ J("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ J("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${a(s)}`,
				onClick: () => t(s.id),
				children: /* @__PURE__ */ J("img", {
					src: un(s),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ J("div", { children: [
				/* @__PURE__ */ J("h3", { children: /* @__PURE__ */ J("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => t(s.id),
					dangerouslySetInnerHTML: { __html: i(s) }
				}) }),
				/* @__PURE__ */ J("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ J("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: o(s.location, s.cost) }
						}),
						/* @__PURE__ */ J("span", { children: e[s.location] ?? s.location }),
						/* @__PURE__ */ J("span", { children: n(s.duration) }),
						/* @__PURE__ */ J("span", { children: r(s.size ?? 0) })
					]
				}),
				s.reason ? /* @__PURE__ */ J("p", { children: s.reason }) : null
			] })]
		}, s.id))
	}) : /* @__PURE__ */ J("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: l("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function fn(e) {
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
function pn(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	fn({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (a.message || (e.title ? e.title + (a.total ? `：已完成 ${a.checked || 0}/${a.total}` : "") : "") || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
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
var mn = (e, t) => z("/api/scraping", t);
function hn({ value: e, onChange: t }) {
	let n = q(null), r = q(t);
	return r.current = t, K(() => {
		let t = n.current;
		t.innerHTML = h([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = y(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ J("div", {
		ref: n,
		class: "scraping-network"
	});
}
function gn({ source: e, toast: t }) {
	let [n, r] = W(e), [i, a] = W(e.network), [o, s] = W(""), [c, l] = W(""), [d, p] = W("paste"), [m, h] = W(""), [g, v] = W(!1), [y, b] = W(""), [x, S] = W([]), C = q(null), w = q(null);
	K(() => {
		w.current?.querySelectorAll("footer button").forEach((e) => _(e, g));
	}, [g]);
	let T = q(new AbortController());
	G(() => () => T.current.abort(), []);
	async function E(n) {
		if (!g) {
			v(!0), b(""), S([]);
			try {
				if (n === "check") {
					let t = await B("/api/scraping/check", { source: e.source }, "POST", T.current.signal);
					T.current.signal.aborted || S(t.results);
				} else {
					let a = await B("/api/scraping/settings", {
						source: e.source,
						network: i,
						cookie: o,
						cookies_text: c,
						revoke: n === "revoke"
					}, "POST", T.current.signal);
					T.current.signal.aborted || (r(a.saved), s(""), l(""), h(""), C.current && (C.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				T.current.signal.aborted || b(R(e));
			} finally {
				T.current.signal.aborted || v(!1);
			}
		}
	}
	return /* @__PURE__ */ J("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ J("form", {
			ref: w,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), E("save");
			},
			children: [/* @__PURE__ */ J("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ J("div", {
						class: "geist-fieldset-heading",
						children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u(`scraping-${e.source}`, e.label) } }), /* @__PURE__ */ J("a", {
							class: "scraping-url",
							href: e.login,
							target: "_blank",
							rel: "noopener noreferrer",
							children: e.login
						})]
					}),
					/* @__PURE__ */ J("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ J(hn, {
							value: i,
							onChange: a
						})]
					}),
					i === "peach" && /* @__PURE__ */ J("a", {
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
								checked: d === t,
								onChange: () => {
									p(t), s(""), l(""), h("");
								}
							}), /* @__PURE__ */ J("span", { children: n })] }, t))
						}),
						d === "paste" ? /* @__PURE__ */ J("label", { children: ["Cookie", /* @__PURE__ */ J("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: o,
							disabled: g,
							onInput: (e) => s(e.currentTarget.value)
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
										children: m || "未选择文件"
									}),
									/* @__PURE__ */ J("input", {
										ref: C,
										type: "file",
										accept: ".txt",
										disabled: g,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												l(""), h("");
												return;
											}
											if (l(""), t.size > 262144) {
												b("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											v(!0);
											try {
												let e = await t.text();
												T.current.signal.aborted || (l(e), h(t.name));
											} catch {
												T.current.signal.aborted || b("Cookie 文件未读取，请重新选择");
											} finally {
												T.current.signal.aborted || v(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					y && /* @__PURE__ */ J("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: f(y, { variant: "error" }) }
					}),
					x.map((t) => /* @__PURE__ */ J("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: f(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ J("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ J("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ J("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void E("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ J("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void E("revoke"),
						children: "撤销 Cookie"
					})
				]
			})]
		})
	});
}
function _n({ data: e, error: t, toast: n }) {
	let [r, i] = W(""), [a, o] = W(!1), [s, c] = W(""), l = q(null);
	K(() => _(l.current, a), [a]);
	let d = q(new AbortController()), p = q(0);
	async function m(e = !1) {
		let t = ++p.current;
		await fn({
			read: (e) => z("/api/scraping/cover", e),
			active: () => !d.current.signal.aborted && t === p.current,
			render: (t) => {
				o(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && c(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => c("连接中断，正在重新读取后台进度")
		});
	}
	G(() => (m(!0), () => d.current.abort()), []);
	async function h() {
		if (!a) {
			p.current++, o(!0), c("");
			try {
				await B("/api/scraping/cover", { code: r }, "POST", d.current.signal), await m();
			} catch (e) {
				d.current.signal.aborted || (o(!1), c(R(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ J("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: f(t, { variant: "error" }) }
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
						/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ J("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), h();
							},
							children: [/* @__PURE__ */ J("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: a,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => i(e.currentTarget.value)
							}), /* @__PURE__ */ J("button", {
								ref: l,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						s && /* @__PURE__ */ J("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: f(s, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ J(gn, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var vn = (e, t) => z("/api/library-processing", t);
function yn({ data: e, error: t, toast: n, onComplete: r, mode: i, monitor: a }) {
	let [o, s] = W(e || { status: "idle" }), [c, l] = W(t), [h, g] = W(!1), [v, y] = W(!1), b = q(new AbortController()), x = q(0), S = q(o.status), C = q(null), w = h || o.status === "running";
	K(() => _(C.current, w), [w]);
	async function T() {
		let e = ++x.current;
		await fn({
			read: (e) => z("/api/library-processing", e),
			active: () => !b.current.signal.aborted && x.current === e,
			keepWatching: i === "notice" || !!a,
			render: (e) => {
				s(e), l(""), e.status === "complete" && S.current === "running" && i !== "notice" && (y(!0), n("已完成扫描与资料采集")), S.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), S.current = e.status;
			},
			disconnected: () => l("连接中断，正在重新读取处理进度")
		});
	}
	G(() => ((o.status === "running" || i === "notice" || a) && T(), () => b.current.abort()), []);
	async function E() {
		if (!w) {
			g(!0), l(""), y(!1);
			try {
				let e = await B("/api/library-processing", {}, "POST", b.current.signal);
				if (b.current.signal.aborted) return;
				S.current = e.status, s(e), g(!1), await T();
			} catch (e) {
				b.current.signal.aborted || (l(R(e)), g(!1));
			}
		}
	}
	if (i === "notice") {
		if (!c && o.status !== "running" && o.status !== "failed") return null;
		let e = c || (o.status === "failed" ? "扫描与资料采集未完成" : `${o.stage || "正在整理馆藏"}${o.total ? ` · ${o.checked || 0} / ${o.total}` : ""}`);
		return /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: m(e, {
			variant: o.status === "failed" ? "error" : c ? "warning" : "gray",
			href: "/data-cleanup#libraryProcessing",
			label: c || o.status === "failed" ? "查看并处理" : "查看进度",
			value: o.checked || 0,
			...o.status === "running" && o.total !== void 0 ? { max: o.total } : {}
		}) } });
	}
	return /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: u("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ J("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ J("div", {
				"aria-live": "polite",
				children: [
					o.status === "running" && /* @__PURE__ */ J(I, { children: [/* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: d(`${o.stage || "正在处理"}${o.total ? ` · ${o.checked || 0} / ${o.total}` : ""}`) } }), !!o.total && /* @__PURE__ */ J("div", { dangerouslySetInnerHTML: { __html: p(`已处理 ${o.checked || 0} / ${o.total} 个视频`, o.checked || 0, o.total) } })] }),
					(c || o.status === "failed") && /* @__PURE__ */ J("div", {
						role: "alert",
						onClick: (e) => {
							e.target.closest("[data-note-action]") && E();
						},
						dangerouslySetInnerHTML: { __html: f(c || o.error || "处理未完成，请重试", {
							variant: "error",
							filled: !0,
							actionLabel: o.status === "failed" ? "重试未完成项" : ""
						}) }
					}),
					o.status === "failed" && !!o.issues?.length && /* @__PURE__ */ J("ul", { children: o.issues.slice(0, 20).map((e) => /* @__PURE__ */ J("li", { children: [
						e.asset_id ? /* @__PURE__ */ J("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					v && /* @__PURE__ */ J("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: f(`已扫描 ${o.scanned || 0} 个文件，识别 ${o.identified || 0} 个番号，整理 ${o.candidates || 0} 组资料候选。`, {
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
			!!o.candidates && /* @__PURE__ */ J("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			o.status !== "failed" && /* @__PURE__ */ J("button", {
				ref: C,
				type: "button",
				class: "geist-button primary",
				onClick: () => void E(),
				children: "扫描并补全资料"
			})
		]
	})] });
}
//#endregion
//#region src/state/index.ts
var bn = { "quality-goals": {
	refresh: cn,
	reset: sn
} }, xn = () => Object.keys(bn);
async function Sn(e) {
	let t = bn[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-evidence.ts
var Cn = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function wn(e = "") {
	let n = Cn(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${n ? " hidden" : ""}>未取得来源图片</span>${n ? `<img src="${t(n)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function Tn(e) {
	let n = Cn(e.profile_url), r = (e.preview_assets || []).slice(0, 6), i = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${t(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${n ? `<a class="geist-button" href="${t(n)}" target="_blank" rel="noopener noreferrer">来源资料 ↗</a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${t(e.creator || "")}">查看全部 ${i.toLocaleString()} 部作品</button></div>
    ${wn(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${r.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${r.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${t(e.name)}">${t(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${t(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function En(e) {
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
var Dn = () => ({
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
function On(e) {
	let t = e?.querySelector(".reviewcontrols");
	if (!e || !t || t.offsetParent === null) return;
	let n = e.closest("main");
	n && e.style.setProperty("--review-edge", getComputedStyle(n).paddingLeft), e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	for (let n of [t, ...e.querySelectorAll(".reviewgroupbar")]) {
		let e = parseFloat(getComputedStyle(n).top);
		n.classList.toggle("is-stuck", n.offsetParent !== null && window.scrollY > 0 && Number.isFinite(e) && Math.abs(n.getBoundingClientRect().top - e) <= 1);
	}
}
function kn(e, t) {
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
function An(e, t) {
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
function jn(e, t, n, r, i) {
	let a = e.anchor === null ? -1 : t.indexOf(e.anchor), o = t.indexOf(n);
	r && a >= 0 && o >= 0 ? t.slice(Math.min(a, o), Math.max(a, o) + 1).forEach((t) => e.selected.add(t)) : i ? e.selected.add(n) : e.selected.delete(n), e.anchor = n;
}
async function Mn(e, t, n, r) {
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
function Nn(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Pn(e, t) {
	let n = e.querySelector(".reviewlist");
	if (!n || !t.rows.length || t.locked) return;
	let r = t.state, i = [...n.querySelectorAll("[data-review-key]")];
	t.category !== void 0 && r.category !== t.category && (r.category = t.category, r.filter = "", r.groupBy = "candidates", r.anchor = null);
	let a = kn(t.rows, t.metadata);
	a.some((e) => e[0] === r.groupBy) || (r.groupBy = "candidates", r.filter = "");
	let o = An(t.rows, r.groupBy);
	o.some((e) => e.key === r.filter) || (r.filter = "");
	let c = () => [...n.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), l = () => c().filter((e) => r.selected.has(e.dataset.reviewKey)), u = () => t.rows.filter((e) => l().some((t) => t.dataset.reviewKey === e.item_key)), d = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, f = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, p = document.createElement("div");
	p.className = "reviewbulkbar reviewbulktoolbar", p.setAttribute("role", "group"), p.setAttribute("aria-label", "复核批量操作");
	let m = document.createElement("div");
	m.className = "reviewgroupby", m.innerHTML = h(a, r.groupBy, { label: "筛选分组方式" });
	let g = y(m.firstElementChild);
	m.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), g.addEventListener("change", () => {
		if (r.busy || !a.some((e) => e[0] === g.value)) return;
		r.groupBy = g.value, r.filter = "", r.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let v = document.createElement("div");
	v.className = "reviewcategoryfilter", v.hidden = o.length < 2, v.innerHTML = h([[
		"",
		"全部分类",
		"list-filter"
	], ...o.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], r.filter, { label: r.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let b = v.querySelector("[data-select-menu]");
	if (b) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", r.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(b.children).slice(1)), b.append(e);
	}
	let x = y(v.firstElementChild);
	v.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), x.addEventListener("change", () => {
		if (r.busy || x.value && !o.some((e) => e.key === x.value)) return;
		r.filter = x.value, r.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let S = f("全选本页"), C = f("通过所选", "primary"), w = f("拒绝所选", "error"), T = document.createElement("span");
	T.className = "reviewselectedcount selectiondockcount", T.setAttribute("role", "status");
	let E = document.createElement("div");
	E.className = "reviewbulksource", E.hidden = !t.metadata;
	let D = document.createElement("p");
	D.className = "reviewstate reviewbulkfeedback", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulkdecisions", O.append(C, w);
	let k = document.createElement("div");
	k.className = "selectiondock reviewdock", k.setAttribute("role", "group"), k.setAttribute("aria-label", "复核所选项目");
	let A = f("取消选择");
	k.append(T, E, O, A, D), p.append(m, v, S);
	let ee = e.querySelector(".reviewcontrols");
	ee ? ee.append(p) : n.before(p), e.append(k), n.classList.add("reviewgroups");
	let j = () => {
		r.selected.clear(), r.anchor = null, P();
	};
	A.onclick = () => {
		r.busy || (j(), S.focus({ preventScroll: !0 }));
	}, S.onclick = () => {
		if (r.busy) return;
		let e = c(), t = l().length === e.length;
		e.forEach((e) => t ? r.selected.delete(e.dataset.reviewKey) : r.selected.add(e.dataset.reviewKey)), P();
	}, C.onclick = () => te("approved", C), w.onclick = () => te("rejected", w);
	let M = [];
	for (let e of o) {
		let t = e.rows.map((e) => i.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e), a = document.createElement("section");
		a.className = "reviewgroup", a.hidden = !!r.filter && e.key !== r.filter;
		let o = document.createElement("div");
		o.className = "reviewbulkbar reviewgroupbar";
		let l = document.createElement("h3");
		l.textContent = `${e.title} · ${t.length}`;
		let u = f("全选本组"), d = document.createElement("div");
		d.className = "reviewlist", o.append(l, u), a.append(o, d), n.append(a), u.onclick = () => {
			if (r.busy) return;
			let e = t.every((e) => r.selected.has(e.dataset.reviewKey));
			t.forEach((t) => e ? r.selected.delete(t.dataset.reviewKey) : r.selected.add(t.dataset.reviewKey)), P();
		}, M.push(() => {
			u.textContent = t.every((e) => r.selected.has(e.dataset.reviewKey)) ? "清空本组" : "全选本组";
		});
		for (let e of t) {
			d.append(e);
			let t = e.dataset.reviewKey;
			r.errors.has(t) && (e.querySelector(".reviewstate").textContent = r.errors.get(t));
			let n = e.querySelector("h4,.reviewentity b") || e, i = document.createElement("label");
			i.className = "reviewpickitem", i.innerHTML = s();
			let a = i.querySelector("input");
			if (a.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || n.textContent || t}`), n !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...n.childNodes), n.classList.add("reviewpickheading"), n.append(i, e);
			} else e.prepend(i);
			let o = (e, n) => {
				jn(r, c().map((e) => e.dataset.reviewKey), t, e, n), P();
			};
			if (i.addEventListener("mousedown", (e) => {
				e.shiftKey && e.preventDefault();
			}), i.addEventListener("click", (e) => {
				e.target !== a && (e.preventDefault(), r.busy || (a.focus(), o(e.shiftKey, !a.checked)));
			}), a.addEventListener("click", (e) => {
				r.busy || o(e.shiftKey, a.checked);
			}), a.addEventListener("keydown", (n) => {
				if (!(r.busy || !n.shiftKey)) {
					if (n.key === " ") n.preventDefault(), o(!0, !0);
					else if (n.key === "ArrowDown" || n.key === "ArrowUp") {
						n.preventDefault();
						let i = c(), a = i[i.indexOf(e) + (n.key === "ArrowDown" ? 1 : -1)];
						a && (r.anchor === null && (r.anchor = t), jn(r, i.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), P(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), M.push(() => {
				a.checked = r.selected.has(t);
			}), r.assets.has(t)) {
				let n = r.assets.get(t), i = [...e.querySelectorAll("[data-review-asset]")];
				i.forEach((e) => {
					let t = n.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(t)), e.classList.toggle("picked", t);
				});
				let a = e.querySelector("[data-picked-count]");
				a && (a.textContent = `已选 ${n.length} / ${i.length}`);
			}
			e.addEventListener("click", (n) => {
				n.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && r.assets.set(t, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let n of e.querySelectorAll("input[type=\"radio\"]")) r.choices.has(t) && (n.checked = r.choices.get(t) === n.value), n.addEventListener("change", () => {
				n.checked && r.choices.set(t, n.value), P();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		r.busy || !e.contains(n) || (t.key === "Escape" && r.selected.size && (t.preventDefault(), t.stopPropagation(), j()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), c().forEach((e) => r.selected.add(e.dataset.reviewKey)), P()));
	});
	let N = "";
	function P() {
		let e = l();
		S.textContent = e.length === c().length ? "清空当前选择" : r.filter ? "全选当前分类" : "全选本页", k.hidden = !e.length, T.textContent = `已选 ${e.length} 项`, C.disabled = !e.length || e.some((e) => !d(e)), w.disabled = !e.length;
		let n = Nn(u());
		E.hidden = !t.metadata || !u().some((e) => (e.candidates?.length || 0) > 1);
		let i = e.length && !n.length ? "所选项目无共同来源" : "统一选择来源", a = JSON.stringify([i, n]);
		if (a !== N) {
			N = a, E.innerHTML = h([["", i], ...n.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = y(E.firstElementChild);
			e.disabled = !n.length, e.addEventListener("change", () => {
				if (!(r.busy || !Nn(u()).includes(e.value))) {
					for (let n of l()) {
						let i = t.rows.find((e) => e.item_key === n.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						n.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === i.candidate_key;
						}), r.choices.set(n.dataset.reviewKey, i.candidate_key);
					}
					D.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		M.forEach((e) => e());
	}
	async function te(n, i) {
		if (r.busy || !l().length) return;
		let a = l().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...t.payload(e),
				status: n
			}
		}));
		if (n === "approved" && t.metadata && a.some((e) => !e.payload.candidate_key)) {
			D.textContent = "请先为所选的多来源候选选择来源。", l().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		r.busy = !0, D.textContent = `正在处理 0 / ${a.length}`, _(i, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let u = 0, d = await Mn(a, async (e) => {
			try {
				return await t.submit(e);
			} finally {
				u++, t.active() && (D.textContent = `正在处理 ${u} / ${a.length}`);
			}
		}, (e) => {
			r.selected.delete(e), r.errors.delete(e), t.applied(e);
		}, t.active);
		if (r.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), _(i, !1), !t.active()) return;
		t.notify(`已${n === "approved" ? "通过" : "拒绝"} ${d.completed} 项${d.failures.length ? `，${d.failures.length} 项未完成` : ""}`), d.failures.forEach((e) => r.errors.set(e.key, e.message));
		let f = e.parentElement;
		t.refresh(), f?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	P(), On(e);
}
//#endregion
//#region src/native-image.ts
function Fn(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function In(e, t, n, r, i = 1) {
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
function Ln(e, t) {
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
var Rn = [
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
function zn() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function Bn(e, t) {
	let n = new URLSearchParams();
	for (let t of Rn) e[t] && n.set(t, e[t]);
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
function Vn({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: r = !1, online: i = !1 } = {}) {
	let a = r ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", o = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	return t || n ? l("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" }) : e === "catalog" ? l("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: a + o }) : l(e === "tags" ? "tags" : "user-round", "还没有" + ({
		tags: "标签",
		performers: "艺人",
		creators: "创作者",
		studios: "厂牌",
		agencies: "事务所",
		series: "系列"
	}[e] || "资料"), i ? "添加关注来源并获取内容后，这里会显示对应标签。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: i ? o : a + o });
}
//#endregion
//#region src/sidebar.ts
function Hn(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Un(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Wn(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function Gn(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function Kn(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function qn() {
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
function Jn(e, t = !1, n = !1) {
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
var Yn = "peach-taste-guide-dismissed";
function Xn(e, t) {
	v(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Yn, "1"), n.remove();
	});
}
//#endregion
//#region src/resource-sync.ts
var $ = (e = 0) => Number(e).toLocaleString(), Zn = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
};
function Qn(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="resourcepanel" data-geist-fieldset><div class="resourcesources">${(e.sources || []).map((e) => `<article>
    <div class="resourcesourcetitle"><b>${Zn[e.location] || "媒体来源"}</b><span class="${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span></div>
    <strong>${e.online ? `${$(e.missing)} 项` : "—"}</strong>
    <small>${e.online ? `找不到文件 · 已检查 ${$(e.checked)} 项` : `馆藏中有 ${$(e.total)} 项`}</small>
    ${e.unreadable ? `<small>${$(e.unreadable)} 项读取失败，已跳过</small>` : ""}</article>`).join("")}</div>
    <div class="resourcecache"><div><span>可清理的缓存</span><b>${$(n.files)} 个</b><small>${t(n.bytes)}</small></div>
    <div><span>待移入回收站</span><b>${$(e.missing)} 项</b></div></div>
    ${r ? f(`将把找不到文件的 ${$(e.missing)} 项馆藏记录移入回收站，并清理 ${$(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div></div>`;
}
//#endregion
//#region src/jav-artwork.ts
function $n(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function er(e) {
	return {
		javLayout: $n(e.javLayout),
		javImage: tr(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function tr(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function nr(e, t) {
	return e.is_jav && e.code && e.has_cover && (tr(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function rr(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (tr(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var ir = {
	"library-processing": {
		load: vn,
		component: yn
	},
	scraping: {
		load: mn,
		component: _n
	},
	"quality-goals": {
		load: ln,
		component: dn
	},
	configuration: {
		load: pt,
		component: bt
	}
}, ar = () => Object.keys(ir), or = /* @__PURE__ */ new Map();
async function sr(e, t, n, r = {}) {
	let i = ir[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	cr(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	or.set(t, a);
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
	if (or.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		or.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	De(ae(i.component, s), t);
}
function cr(e) {
	let t = or.get(e);
	t && (t.controller.abort(), or.delete(e), t.painted && De(null, e));
}
//#endregion
export { Yn as TASTE_GUIDE_KEY, Vn as catalogEmptyHtml, Bn as catalogSuggestions, qn as cleanupSkeletonHtml, Gn as cloudLocations, Kn as cloudPreferenceLocations, Dn as createReviewSelection, zn as emptyCatalogLayout, Ln as entitySkeletonHtml, pn as followJobProgress, Tn as identityEvidenceHtml, ar as islandNames, nr as javImageKind, Fn as matchesFaceSource, sr as mountIsland, In as nativeImageFit, tr as normalizeJavImage, $n as normalizeJavLayout, er as normalizeJavPreferences, Oe as preferredDirection, Sn as refreshStore, Qn as resourceScanHtml, wn as reviewImageHtml, Hn as sidebarHasCatalogContent, Wn as sidebarTagCounts, xn as storeNames, rr as syncJavImages, Un as syncSidebarSurface, Jn as tasteHistoryGuideHtml, cr as unmountIsland, On as updateReviewSticky, fn as watchJob, En as wireReviewPictures, Pn as wireReviewSelection, Xn as wireTasteHistoryGuide };
