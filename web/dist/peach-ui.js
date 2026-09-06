import { MEDIA_SOURCE_ICONS as e, badgeHtml as t, checkboxHtml as n, confirmModal as r, emptyStateHtml as i, fieldsetTitle as a, loadingDotsHtml as o, noteHtml as s, progressHtml as c, selectFieldHtml as l, selectOptionIconHtml as u, setActionBusy as d, wireCollapse as f, wireSelectField as p } from "/js/ui-components.js";
import { LOC as m, fmtDur as h, fmtSize as g, icon as _ } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var v, y, b, x, S, C, w, T, E, D, O, k, A, ee, te, j = {}, ne = [], re = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, ie = Array.isArray;
function M(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ae(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function oe(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? v.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return se(e, o, r, i, null);
}
function se(e, t, n, r, i) {
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
		__v: i ?? ++b,
		__i: -1,
		__u: 0
	};
	return i == null && y.vnode != null && y.vnode(a), a;
}
function N(e) {
	return e.children;
}
function ce(e, t) {
	this.props = e, this.context = t;
}
function P(e, t) {
	if (t == null) return e.__ ? P(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? P(e) : null;
}
function le(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = M({}, t);
		a.__v = t.__v + 1, y.vnode && y.vnode(a), be(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? P(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, Se(r, a, i), t.__e = t.__ = null, a.__e != n && ue(a);
	}
}
function ue(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), ue(e);
}
function de(e) {
	(!e.__d && (e.__d = !0) && S.push(e) && !fe.__r++ || C != y.debounceRendering) && ((C = y.debounceRendering) || w)(fe);
}
function fe() {
	try {
		for (var e, t = 1; S.length;) S.length > t && S.sort(T), e = S.shift(), t = S.length, le(e);
	} finally {
		S.length = fe.__r = 0;
	}
}
function pe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || ne, v = t.length;
	for (c = me(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || j, p.__i = d, g = be(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && Te(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = he(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function me(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = se(null, o, null, null, null) : ie(o) ? o = e.__k[a] = se(N, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = se(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = ge(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = P(s)), Ee(s, s));
	return r;
}
function he(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = he(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = P(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function ge(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function _e(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || re.test(t) ? n : n + "px";
}
function ve(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || _e(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || _e(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(k, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[O] = r[O] : (n[O] = A, e.addEventListener(t, a ? te : ee, a)) : e.removeEventListener(t, a ? te : ee, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ye(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[D] == null) t[D] = A++;
			else if (t[D] < n[O]) return;
			return n(y.event ? y.event(t) : t);
		}
	};
}
function be(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, b, x, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = y.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, b = D.prototype && D.prototype.render, x = (u = D.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (b ? t.__c = f = new D(v, S) : (t.__c = f = new ce(v, S), f.constructor = D, f.render = De), x && x.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), b && f.__s == null && (f.__s = f.state), b && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = M({}, f.__s)), M(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) b && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), b && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (b && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, S)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), ne.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = P(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(v, f.__s, S), b && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, g);
				});
			}
			if (f.context = S, f.props = v, f.__P = e, f.__e = !1, C = y.__r, w = 0, b) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), ne.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = M(M({}, r), f.getChildContext())), b && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === N && u.key == null ? Ce(u.props.children) : u, s = pe(e, ie(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ae(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || xe(t), y.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = we(n.__e, t, n, r, i, a, o, c, l);
	return (u = y.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function xe(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(xe));
}
function Se(e, t, n) {
	for (var r = 0; r < n.length; r++) Te(n[r], n[++r], n[++r]);
	y.__c && y.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			y.__e(e, t.__v);
		}
	});
}
function Ce(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : ie(e) ? e.map(Ce) : e.constructor === void 0 ? M({}, e) : null;
}
function we(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h, g = n.props || j, _ = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!b && (b ? p.localName == b : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(_);
		e = document.createElementNS(i, b, _.is && _), s &&= (y.__m && y.__m(t, a), !1), a = null;
	}
	if (b == null) g === _ || s && e.data == _ || (e.data = _);
	else {
		if (a = b == "textarea" && _.defaultValue != null ? null : a && v.call(e.childNodes), !s && a != null) for (g = {}, l = 0; l < e.attributes.length; l++) g[(p = e.attributes[l]).name] = p.value;
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || ve(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || ve(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), pe(t.type == "template" ? e.content : e, ie(f) ? f : [f], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && P(n, 0), s, c), a != null) for (l = a.length; l--;) ae(a[l]);
		s && b != "textarea" || (l = "value", b == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || b == "progress" && !m || b == "option" && m != g[l]) && ve(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && ve(e, l, h, g[l], i));
	}
	return e;
}
function Te(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		y.__e(e, n);
	}
}
function Ee(e, t, n) {
	var r, i;
	if (y.unmount && y.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || Te(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			y.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && Ee(r[i], t, n || typeof e.type != "function");
	n || ae(e.__e), e.__c = e.__ = e.__e = void 0;
}
function De(e, t, n) {
	return this.constructor(e, n);
}
function Oe(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), y.__ && y.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], be(t, e = (!r && n || t).__k = oe(N, null, [e]), i || j, j, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? v.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), Se(a, e, o), e.props.children = null;
}
v = ne.slice, y = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, b = 0, x = function(e) {
	return e != null && e.constructor === void 0;
}, ce.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = M({}, this.state);
	typeof e == "function" && (e = e(M({}, n), this.props)), e && M(n, e), e != null && this.__v && (t && this._sb.push(t), de(this));
}, ce.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), de(this));
}, ce.prototype.render = N, S = [], w = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, T = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, fe.__r = 0, E = Math.random().toString(8), D = "__d" + E, O = "__a" + E, k = /(PointerCapture)$|Capture$/i, A = 0, ee = ye(!1), te = ye(!0);
//#endregion
//#region src/sort-preferences.ts
function ke(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/api.ts
var Ae = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, je = (e) => {
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
}, F = (e) => e instanceof Error ? e.message : String(e);
async function I(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Ae(je(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function L(e, t, n = "POST", r) {
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
	if (!i.ok) throw new Ae(je(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var R, z, Me, Ne, Pe = 0, Fe = [], B = y, Ie = B.__b, Le = B.__r, Re = B.diffed, ze = B.__c, Be = B.unmount, Ve = B.__;
function He(e, t) {
	B.__h && B.__h(z, e, Pe || t), Pe = 0;
	var n = z.__H || (z.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function V(e) {
	return Pe = 1, Ue(Ze, e);
}
function Ue(e, t, n) {
	var r = He(R++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Ze(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = z, !z.__f)) {
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
		z.__f = !0;
		var a = z.shouldComponentUpdate, o = z.componentWillUpdate;
		z.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, z.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function H(e, t) {
	var n = He(R++, 3);
	!B.__s && Xe(n.__H, t) && (n.__ = e, n.u = t, z.__H.__h.push(n));
}
function U(e, t) {
	var n = He(R++, 4);
	!B.__s && Xe(n.__H, t) && (n.__ = e, n.u = t, z.__h.push(n));
}
function W(e) {
	return Pe = 5, We(function() {
		return { current: e };
	}, []);
}
function We(e, t) {
	var n = He(R++, 7);
	return Xe(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Ge() {
	for (var e; e = Fe.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Je), t.__h.some(Ye), t.__h = [];
		} catch (n) {
			t.__h = [], B.__e(n, e.__v);
		}
	}
}
B.__b = function(e) {
	z = null, Ie && Ie(e);
}, B.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Ve && Ve(e, t);
}, B.__r = function(e) {
	Le && Le(e), R = 0;
	var t = (z = e.__c).__H;
	t && (Me === z ? (t.__h = [], z.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Je), t.__h.some(Ye), t.__h = [], R = 0)), Me = z;
}, B.diffed = function(e) {
	Re && Re(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Fe.push(t) !== 1 && Ne === B.requestAnimationFrame || ((Ne = B.requestAnimationFrame) || qe)(Ge)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Me = z = null;
}, B.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Je), e.__h = e.__h.filter(function(e) {
				return !e.__ || Ye(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], B.__e(n, e.__v);
		}
	}), ze && ze(e, t);
}, B.unmount = function(e) {
	Be && Be(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Je(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && B.__e(t, n.__v));
};
var Ke = typeof requestAnimationFrame == "function";
function qe(e) {
	var t, n = function() {
		clearTimeout(r), Ke && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Ke && (t = requestAnimationFrame(n));
}
function Je(e) {
	var t = z, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), z = t;
}
function Ye(e) {
	var t = z;
	e.__c = e.__(), z = t;
}
function Xe(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function Ze(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var Qe = 0;
Array.isArray;
function G(e, t, n, r, i, a) {
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
		__v: --Qe,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return y.vnode && y.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function $e({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1 }) {
	return /* @__PURE__ */ G("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ G("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ G("input", {
				id: e,
				class: "geist-input",
				type: "password",
				autoComplete: o ? "current-password" : "new-password",
				maxLength: 256,
				value: n,
				onInput: (e) => r(e.currentTarget.value),
				required: !0,
				"aria-invalid": !!i,
				"aria-describedby": i || a ? `${e}-hint` : void 0
			}),
			i || a ? /* @__PURE__ */ G("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function et({ initial: e, receipt: t }) {
	let [n, r] = V(e), [i, o] = V(""), [s, c] = V(""), [l, u] = V(""), [f, p] = V(!1), [m, h] = V(""), [g, _] = V({}), v = W(null), y = W(!1), b = W(null);
	return /* @__PURE__ */ G("form", {
		class: "configfieldset",
		onSubmit: async (e) => {
			if (e.preventDefault(), y.current) return;
			h("");
			let a = {};
			if (n.mode === "password" && !i && (a.current_password = "请输入当前访问密码"), f || ((s.length < 8 || s.length > 256) && (a.password = "访问密码需为 8–256 个字符"), s !== l && (a.confirmation = "两次输入的密码不一致")), _(a), Object.keys(a).length) {
				requestAnimationFrame(() => v.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			y.current = !0, d(b.current, !0);
			try {
				let e = await L("/api/configuration/access", {
					revision: n.revision,
					action: f ? "disable" : "set",
					confirm_disable: f,
					current_password: i,
					password: f ? "" : s,
					confirmation: f ? "" : l
				});
				r(e), o(""), c(""), u(""), p(!1), _({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof Ae ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? _(n) : h(F(e));
			} finally {
				y.current = !1, d(b.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: v,
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("accessTitle", "访问密码") } }), /* @__PURE__ */ G("p", {
						class: "confighelp",
						children: n.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : n.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : n.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
					})]
				}),
				n.mode === "password" ? /* @__PURE__ */ G($e, {
					id: "access-current",
					label: "当前访问密码",
					value: i,
					onInput: o,
					error: g.current_password,
					current: !0
				}) : null,
				!f && n.mode !== "locked" ? /* @__PURE__ */ G(N, { children: [/* @__PURE__ */ G($e, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: s,
					onInput: c,
					error: g.password,
					help: "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ G($e, {
					id: "access-confirm",
					label: "确认访问密码",
					value: l,
					onInput: u,
					error: g.confirmation
				})] }) : null,
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ G("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ G("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ G("input", {
							type: "checkbox",
							checked: f,
							onChange: (e) => p(e.currentTarget.checked)
						}), /* @__PURE__ */ G("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ G("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ G("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ G("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				m ? /* @__PURE__ */ G("p", {
					class: "configbad",
					role: "alert",
					children: m
				}) : null
			]
		}), n.mode === "locked" ? null : /* @__PURE__ */ G("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ G("p", { children: "保存后立即生效。" }), /* @__PURE__ */ G("button", {
				class: "geist-button primary",
				type: "submit",
				ref: b,
				children: "保存配置"
			})]
		})]
	});
}
//#endregion
//#region src/islands/release-updates.tsx
var tt = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function nt({ initial: e, initialJob: t }) {
	let [n, i] = V(e), [o, s] = V(t || {
		state: "idle",
		progress: 0
	}), [l, u] = V(""), f = W(null), p = W(!0), m = W(!1), h = W(null);
	H(() => {
		d(h.current, tt.has(o.state));
	}, [o.state]), H(() => () => {
		p.current = !1, f.current?.abort();
	}, []);
	let g = async () => {
		let e = await L("/api/configuration/update-restart", {});
		p.current && s(e);
	};
	H(() => {
		o.state !== "ready" || m.current || (m.current = !0, r({
			title: "更新已准备好",
			body: `Peach ${o.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: g
		}));
	}, [o.state]), H(() => {
		if (!tt.has(o.state)) return;
		let e = new AbortController(), t, n = 0, r = async () => {
			try {
				let t = await I("/api/configuration/update-status", e.signal);
				e.signal.aborted || (s(t), n = 0, t.state === "complete" && i((e) => ({
					...e,
					current_version: t.version || e.current_version,
					state: "current",
					message: "已是最新测试版。"
				})));
			} catch {
				++n >= 120 && !e.signal.aborted && u("尚未连接到 Peach，请检查托盘后刷新页面。");
			}
			!e.signal.aborted && n < 120 && (t = setTimeout(r, 1e3));
		};
		return t = setTimeout(r, 1e3), () => {
			e.abort(), clearTimeout(t);
		};
	}, [o.state]);
	let _ = async (e) => {
		if (f.current || tt.has(o.state)) return;
		let t = new AbortController();
		f.current = t, m.current = !1, u(""), d(e, !0);
		try {
			let e = await L("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || s(e);
		} catch (e) {
			t.signal.aborted || u(F(e));
		} finally {
			f.current = null, d(e, !1);
		}
	}, v = async (t) => {
		if (f.current) return;
		let n = new AbortController();
		f.current = n, d(t, !0), u("");
		try {
			let e = await I("/api/configuration/updates", n.signal);
			n.signal.aborted || i(e);
		} catch (t) {
			n.signal.aborted || (i({
				...e,
				state: "error"
			}), u(F(t)));
		} finally {
			f.current = null, d(t, !1);
		}
	};
	return /* @__PURE__ */ G("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ G("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ G("dt", { children: "当前版本" }),
						/* @__PURE__ */ G("dd", { children: n.current_version }),
						/* @__PURE__ */ G("dt", { children: "安装方式" }),
						/* @__PURE__ */ G("dd", { children: n.installation }),
						/* @__PURE__ */ G("dt", { children: "更新通道" }),
						/* @__PURE__ */ G("dd", { children: n.channel }),
						/* @__PURE__ */ G("dt", { children: "最新版本" }),
						/* @__PURE__ */ G("dd", { children: n.latest_version || (n.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				/* @__PURE__ */ G("p", {
					class: l || n.state === "error" ? "configbad" : "confighelp",
					role: l || n.state === "error" ? "alert" : "status",
					children: l || n.message
				}),
				o.state === "idle" ? null : /* @__PURE__ */ G("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ G("p", {
						class: o.state === "error" ? "configbad" : "confighelp",
						children: o.message
					}), o.state === "error" ? null : /* @__PURE__ */ G(N, { children: [/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: c(o.state === "downloading" ? "下载进度" : "安装进度", o.state === "downloading" ? o.downloaded || 0 : o.progress, o.state === "downloading" ? o.total || 1 : 100) } }), /* @__PURE__ */ G("p", {
						class: "confighelp",
						children: o.state === "downloading" && o.total ? `${((o.downloaded || 0) / 1048576).toFixed(1)} / ${(o.total / 1048576).toFixed(1)} MB` : `${o.progress}%`
					})] })]
				})
			]
		}), /* @__PURE__ */ G("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ G("a", {
					class: "geist-button",
					href: n.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: "查看发布页"
				}),
				o.state === "ready" ? /* @__PURE__ */ G("button", {
					type: "button",
					class: "geist-button primary",
					onClick: () => {
						r({
							title: "更新已准备好",
							body: `Peach ${o.version || ""} 将在重启后安装。`,
							confirmLabel: "立即重启",
							cancelLabel: "稍后",
							onConfirm: g
						});
					},
					children: "重启安装"
				}) : null,
				n.state === "available" && n.installation === "独立测试包" && o.state !== "ready" ? /* @__PURE__ */ G("button", {
					ref: h,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => _(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ G("button", {
					type: "button",
					class: "geist-button",
					disabled: tt.has(o.state),
					onClick: (e) => v(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function rt({ initial: e, receipt: t }) {
	let [n, r] = V(e), [i, o] = V(e.mode), [s, c] = V(""), [u, f] = V(""), m = W(!1), h = W(null), g = W(null), _ = W(new AbortController());
	H(() => () => _.current.abort(), []), U(() => {
		let t = h.current;
		t.innerHTML = l([
			["environment", "系统代理"],
			["direct", "直连"],
			["proxy", "自定义"]
		], e.mode, {
			label: "Peach 代理",
			className: "configselect",
			attr: "data-fixed-width"
		});
		let n = p(t.firstElementChild), r = () => o(n.value);
		return n.addEventListener("change", r), () => {
			n.removeEventListener("change", r), t.replaceChildren();
		};
	}, []);
	async function v() {
		if (!m.current) {
			m.current = !0, d(g.current, !0), f("");
			try {
				let e = await L("/api/configuration/peach-proxy", {
					mode: i,
					proxy: s
				}, "POST", _.current.signal);
				_.current.signal.aborted || (r(e), c(""), t("已保存 Peach 代理"));
			} catch (e) {
				_.current.signal.aborted || f(F(e));
			} finally {
				m.current = !1, d(g.current, !1);
			}
		}
	}
	return /* @__PURE__ */ G("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), v();
		},
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("peachProxyTitle", "Peach 代理") } }),
				/* @__PURE__ */ G("p", {
					class: "confighelp",
					children: "采集来源选择“Peach 代理”时共用此设置。"
				}),
				/* @__PURE__ */ G("div", { ref: h }),
				i === "proxy" && /* @__PURE__ */ G("div", {
					class: "configfield",
					children: [/* @__PURE__ */ G("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ G("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: s,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => c(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ G("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				u && /* @__PURE__ */ G("p", {
					class: "configbad",
					role: "alert",
					children: u
				})
			]
		}), /* @__PURE__ */ G("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ G("button", {
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
function it({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ G("label", {
		class: "configcheck",
		children: [/* @__PURE__ */ G("span", {
			class: "pcheck",
			children: [/* @__PURE__ */ G("input", {
				type: "checkbox",
				checked: t,
				disabled: n,
				onChange: (e) => r(e.currentTarget.checked)
			}), /* @__PURE__ */ G("span", {
				"aria-hidden": "true",
				children: /* @__PURE__ */ G("svg", {
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ G("use", { href: "#i-check" })
				})
			})]
		}), /* @__PURE__ */ G("span", { children: e })]
	});
}
function at({ startup: e, receipt: t }) {
	let [n, r] = V(e.enabled), [i, o] = V(e.silent), [s, c] = V(""), l = W(!1), u = W(null);
	async function f() {
		if (!l.current) {
			l.current = !0, d(u.current, !0), c("");
			try {
				await L("/api/configuration/startup", {
					enabled: n,
					silent: i
				}), t("已保存开机自启");
			} catch (e) {
				c(F(e));
			} finally {
				l.current = !1, d(u.current, !1);
			}
		}
	}
	return /* @__PURE__ */ G("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), f();
		},
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("startupTitle", "开机自启") } }),
				/* @__PURE__ */ G(it, {
					label: "开机后启动 Peach",
					checked: n,
					disabled: !e.available,
					change: r
				}),
				/* @__PURE__ */ G(it, {
					label: "静默启动",
					checked: i,
					disabled: !e.available,
					change: o
				}),
				/* @__PURE__ */ G("p", {
					class: "confighelp",
					children: "静默启动仅显示托盘；关闭后自动打开浏览器。"
				}),
				e.message && /* @__PURE__ */ G("p", {
					class: "confighelp",
					children: e.message
				}),
				s && /* @__PURE__ */ G("p", {
					class: "configbad",
					role: "alert",
					children: s
				})
			]
		}), /* @__PURE__ */ G("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ G("button", {
				ref: u,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存自启"
			})
		})]
	});
}
function ot({ data: e }) {
	let t = W(null);
	return U(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let i = document.createElement("summary");
		i.innerHTML = _("chevron-right") + "<span>数据目录</span>", r.append(i);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), f(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ G("div", { ref: t });
}
function st({ uninstall: e }) {
	let [t, n] = V(!1), [i, o] = V("");
	async function s() {
		await r({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序和开机自启。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await L("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				o(e.message);
			}
		});
	}
	return /* @__PURE__ */ G("section", {
		id: "uninstallPeach",
		class: "configfieldset configdanger",
		"data-geist-fieldset": !0,
		"data-fieldset-type": "error",
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("uninstallTitle", "卸载 Peach") } }),
				e.available && /* @__PURE__ */ G("p", {
					class: "confighelp",
					children: "卸载会退出 Peach、移除程序和开机自启。原始媒体文件保留。"
				}),
				/* @__PURE__ */ G(it, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!i,
					change: n
				}),
				/* @__PURE__ */ G(ot, { data: e }),
				e.message && /* @__PURE__ */ G("p", {
					class: "confighelp",
					children: e.message
				}),
				i && /* @__PURE__ */ G("p", {
					class: "confighelp",
					role: "status",
					children: i
				})
			]
		}), /* @__PURE__ */ G("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ G("button", {
				type: "button",
				class: "geist-button danger",
				disabled: !e.available || !!i,
				onClick: () => void s(),
				children: "卸载 Peach"
			})
		})]
	});
}
//#endregion
//#region src/islands/configuration.tsx
var ct = "/api/configuration", lt = "/api/pick-folder", ut = 8e3, dt = (e, t) => I(ct, t), K = ({ html: e, class: t }) => /* @__PURE__ */ G("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), ft = (e) => !(e instanceof Ae) || e.status !== 400 ? null : e.body?.errors ?? null;
function pt({ facts: e }) {
	return /* @__PURE__ */ G("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ G(K, { html: a("configFactsTitle", "运行信息") }), /* @__PURE__ */ G("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ G(N, { children: [/* @__PURE__ */ G("dt", { children: e.term }), /* @__PURE__ */ G("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ G("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ G("a", {
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ G("svg", {
							"aria-hidden": "true",
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ G("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function mt({ data: t }) {
	let [n, r] = V(t.media_sources), [i, o] = V(""), s = W(null);
	H(() => () => s.current?.abort(), []);
	let c = async (e) => {
		if (s.current) return;
		let t = new AbortController();
		s.current = t, d(e, !0), o("");
		try {
			let e = await I(ct, t.signal);
			t.signal.aborted || r(e.media_sources);
		} catch (e) {
			t.signal.aborted || o(F(e));
		} finally {
			s.current = null, d(e, !1);
		}
	};
	return n ? /* @__PURE__ */ G("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G(K, { html: a("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ G("dl", {
					class: "configfacts",
					children: n.map((t) => /* @__PURE__ */ G(N, { children: [/* @__PURE__ */ G("dt", { children: [/* @__PURE__ */ G("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: u(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ G("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ G("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				i ? /* @__PURE__ */ G("p", {
					class: "configbad",
					role: "alert",
					children: i
				}) : null
			]
		}), /* @__PURE__ */ G("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ G("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => c(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function ht({ value: t, label: n, onChange: r }) {
	let i = W(null), a = W(null), o = W(r);
	return o.current = r, U(() => {
		let r = i.current;
		r.innerHTML = l([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([t, n]) => [
			t,
			n,
			e[t]
		]), t, { label: n });
		let s = p(r.firstElementChild);
		a.current = s;
		let c = () => o.current(s.value);
		return s.addEventListener("change", c), () => {
			a.current = null, s.disabled = !0, s.removeEventListener("change", c), r.replaceChildren();
		};
	}, [n]), U(() => {
		a.current && (a.current.value = t);
	}, [t]), /* @__PURE__ */ G("div", {
		ref: i,
		class: "configsourcecontrol"
	});
}
function gt({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, i] = V(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [o, c] = V(n?.map((e) => e.location) ?? []), [l, u] = V(n?.map((e) => e.root) ?? []), [f, p] = V(String(e.port)), [m, h] = V(!1), [g, _] = V([]), [v, y] = V(""), [b, x] = V(""), [S, C] = V(null), [w, T] = V(null), E = W(!1), D = W(e.revision), O = W([]), k = W(null);
	U(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), H(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), ut);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		i((n) => n.map((n, r) => r === e ? t : n));
	}, ee = () => {
		T(r.length), i((e) => [...e, ""]);
	}, te = (e) => {
		c((t) => t.filter((t, n) => n !== e)), u((t) => t.filter((t, n) => n !== e)), i((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, j = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, ne = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			d(t, !0);
			try {
				let { path: t } = await L(lt, { initial: r[e] ?? "" });
				t && (A(e, t), j(e, ""));
			} catch (t) {
				j(e, F(t));
			} finally {
				d(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ G("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ G("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ G("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ G("use", { href: "#i-check" })
			}), /* @__PURE__ */ G("p", { children: /* @__PURE__ */ G("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ G("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ G("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !E.current) {
				E.current = !0, d(k.current, !0), x("");
				try {
					let n = await L(ct, {
						revision: D.current,
						media_dirs: r,
						...e.media_sources ? { media_sources: r.map((e, t) => ({
							path: e,
							location: o[t] || "local",
							root: l[t] || ""
						})) } : {},
						port: f,
						scan_now: m
					});
					D.current = n.revision, _([]), y(""), t("已保存配置"), C(n);
				} catch (e) {
					let t = ft(e);
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(F(e)));
				} finally {
					E.current = !1, d(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ G("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ G(K, { html: a("configTitle", "这台电脑") }),
				/* @__PURE__ */ G("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ G("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ G("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: r.map((t, n) => /* @__PURE__ */ G("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ G("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ G("input", {
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
									/* @__PURE__ */ G("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => ne(n, e.currentTarget),
										children: /* @__PURE__ */ G("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ G("use", { href: "#i-folder-search" })
										})
									}),
									r.length > 1 ? /* @__PURE__ */ G("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => te(n),
										children: /* @__PURE__ */ G("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ G("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ G("div", {
										class: "configsource",
										children: [/* @__PURE__ */ G("div", {
											class: "configsourcelabel",
											children: ["媒体来源", /* @__PURE__ */ G(ht, {
												label: `媒体来源 ${n + 1}`,
												value: o[n] || "local",
												onChange: (e) => {
													let t = [...o];
													t[n] = e, c(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ G("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ G("input", {
											class: "geist-input",
											"aria-label": `Windows 中的对应路径 ${n + 1}`,
											value: l[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...l];
												t[n] = e.currentTarget.value, u(t);
											}
										})] }) : null]
									}),
									g[n] ? /* @__PURE__ */ G("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ G("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: ee,
							children: "添加文件夹"
						}),
						o.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ G("p", {
							class: "confighelp",
							children: ["先在 CloudDrive 登录网盘并完成挂载。", /* @__PURE__ */ G("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: ["挂载帮助", /* @__PURE__ */ G("svg", {
									"aria-hidden": "true",
									viewBox: "0 0 24 24",
									children: /* @__PURE__ */ G("use", { href: "#i-external-link" })
								})]
							})]
						}) : null,
						o.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ G("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ G("a", {
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ G("svg", {
											"aria-hidden": "true",
											viewBox: "0 0 24 24",
											children: /* @__PURE__ */ G("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ G("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ G("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ G("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ G("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ G("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ G("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ G("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ G("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ G("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ G("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ G("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ G("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ G("span", { children: "保存后扫描并补全资料" })]
				}),
				b ? /* @__PURE__ */ G(K, { html: s(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ G("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ G("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ G("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function _t({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ G(K, {
		class: "configpage",
		html: s(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ G("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ G(at, {
				startup: t.startup,
				receipt: e
			}) : null,
			t.editable ? /* @__PURE__ */ G(gt, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ G(K, { html: s(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ G(mt, { data: t }),
			t.peach_proxy ? /* @__PURE__ */ G(rt, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ G(et, {
				initial: t.access,
				receipt: e
			}) : null,
			t.updates ? /* @__PURE__ */ G(nt, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ G(pt, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ G(st, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var vt = Symbol.for("preact-signals");
function yt() {
	if (J > 1) J--;
	else {
		var e, t = !1;
		for ((function() {
			var e = Dt;
			for (Dt = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); Ct !== void 0;) {
			var n = Ct;
			for (Ct = void 0, wt++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && jt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (wt = 0, J--, t) throw e;
	}
}
function bt(e) {
	if (J > 0) return e();
	Et = ++Tt, J++;
	try {
		return e();
	} finally {
		yt();
	}
}
var xt, q = void 0;
function St(e) {
	var t = q, n = xt;
	q = void 0, xt = void 0;
	try {
		return e();
	} finally {
		q = t, xt = n;
	}
}
var Ct = void 0, J = 0, wt = 0, Tt = 0, Et = 0, Dt = void 0, Ot = 0;
function kt(e) {
	if (q !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== q) return t = {
			i: 0,
			S: e,
			p: q.s,
			n: void 0,
			t: q,
			e: void 0,
			x: void 0,
			r: t
		}, q.s !== void 0 && (q.s.n = t), q.s = t, e.n = t, 32 & q.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = q.s, t.n = void 0, q.s.n = t, q.s = t), t;
	}
}
function Y(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Y.prototype.brand = vt, Y.prototype.h = function() {
	return !0;
}, Y.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? St(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Y.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && St(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Y.prototype.subscribe = function(e) {
	var t = this;
	return Rt(function() {
		var n = t.value;
		St(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Y.prototype.valueOf = function() {
	return this.value;
}, Y.prototype.toString = function() {
	return this.value + "";
}, Y.prototype.toJSON = function() {
	return this.value;
}, Y.prototype.peek = function() {
	var e = this;
	return St(function() {
		return e.value;
	});
}, Object.defineProperty(Y.prototype, "value", {
	get: function() {
		var e = kt(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (wt > 100) throw Error("Cycle detected");
			(function(e) {
				J !== 0 && wt === 0 && e.l !== Et && (e.l = Et, Dt = {
					S: e,
					v: e.v,
					i: e.i,
					o: Dt
				});
			})(this), this.v = e, this.i++, Ot++, J++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				yt();
			}
		}
	}
});
function At(e, t) {
	return new Y(e, t);
}
function jt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Mt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Nt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function X(e, t) {
	Y.call(this, void 0, t), this.x = e, this.s = void 0, this.g = Ot - 1, this.f = 4;
}
X.prototype = new Y(), X.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === Ot)) return !0;
	if (this.g = Ot, this.f |= 1, this.i > 0 && !jt(this)) return this.f &= -2, !0;
	var e = q;
	try {
		Mt(this), q = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return q = e, Nt(this), this.f &= -2, !0;
}, X.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Y.prototype.S.call(this, e);
}, X.prototype.U = function(e) {
	if (this.t !== void 0 && (Y.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, X.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(X.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = kt(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function Pt(e, t) {
	return new X(e, t);
}
function Ft(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		J++;
		var n = q;
		q = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, It(e), t;
		} finally {
			q = n, yt();
		}
	}
}
function It(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Ft(e);
}
function Lt(e) {
	if (q !== this) throw Error("Out-of-order effect");
	Nt(this), q = e, this.f &= -2, 8 & this.f && It(this), yt();
}
function Z(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, xt && xt.push(this);
}
Z.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Z.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Ft(this), Mt(this), J++;
	var e = q;
	return q = this, Lt.bind(this, e);
}, Z.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = Ct, Ct = this);
}, Z.prototype.d = function() {
	this.f |= 8, 1 & this.f || It(this);
}, Z.prototype.dispose = function() {
	this.d();
};
function Rt(e, t) {
	var n = new Z(e, t);
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
function Q(e, t) {
	y[e] = t.bind(null, y[e] || function() {});
}
function Ut(e) {
	if (Bt) {
		var t = Bt;
		Bt = void 0, t();
	}
	Bt = e && e.S();
}
function Wt(e) {
	var t = this, n = e.data, r = Kt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = We(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = Pt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = Pt(function() {
			return !Array.isArray(i.value) && !x(i.value);
		}), o = Rt(function() {
			if (this.N = Yt, a.value) {
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
Wt.displayName = "ReactiveTextNode", Object.defineProperties(Y.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Wt
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
}), Q("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Y && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Q("__r", function(e, t) {
	if (e(t), t.type !== N) {
		Ut();
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
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Ut(n);
	}
}), Q("__e", function(e, t, n, r) {
	Ut(), e(t, n, r);
}), Q("diffed", function(e, t) {
	Ut();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Gt(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Gt(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = At(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Rt(function() {
			this.N = Yt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Q("unmount", function(e, t) {
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
}), Q("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), ce.prototype.shouldComponentUpdate = function(e, t) {
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
function Kt(e, t) {
	return We(function() {
		return At(e, t);
	}, []);
}
var qt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Jt() {
	bt(function() {
		for (var e; e = Ht.shift();) zt.call(e);
	});
}
function Yt() {
	Ht.push(this) === 1 && (y.requestAnimationFrame || qt)(Jt);
}
//#endregion
//#region src/state/quality-goals.ts
var Xt = "/api/quality-goals?limit=200", Zt = {
	data: null,
	error: ""
}, Qt = At(Zt), $t = 0, en = Pt(() => Qt.value);
Pt(() => Qt.value.data?.total ?? null);
function tn() {
	$t += 1, Qt.value = Zt;
}
async function nn(e) {
	let t = $t += 1;
	try {
		let n = await I(Xt, e);
		return t === $t && (Qt.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === $t && (Qt.value = {
			data: null,
			error: F(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var rn = (e, t) => nn(t), an = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function on({ openItem: e, javTitleHtml: t, javDisplayName: n, srcBadge: r }) {
	let { data: a, error: o } = en.value;
	if (o) return /* @__PURE__ */ G("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: s(o, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let c = a?.items ?? [];
	return c.length ? /* @__PURE__ */ G("div", {
		class: "qualitylist",
		children: c.map((i) => /* @__PURE__ */ G("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ G("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${n(i)}`,
				onClick: () => e(i.id),
				children: /* @__PURE__ */ G("img", {
					src: an(i),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ G("div", { children: [
				/* @__PURE__ */ G("h3", { children: /* @__PURE__ */ G("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(i.id),
					dangerouslySetInnerHTML: { __html: t(i) }
				}) }),
				/* @__PURE__ */ G("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ G("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: r(i.location, i.cost) }
						}),
						/* @__PURE__ */ G("span", { children: m[i.location] ?? i.location }),
						/* @__PURE__ */ G("span", { children: h(i.duration) }),
						/* @__PURE__ */ G("span", { children: g(i.size ?? 0) })
					]
				}),
				i.reason ? /* @__PURE__ */ G("p", { children: i.reason }) : null
			] })]
		}, i.id))
	}) : /* @__PURE__ */ G("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: i("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function sn(e) {
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
function cn(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	sn({
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
var ln = (e, t) => I("/api/scraping", t);
function un({ value: e, onChange: t }) {
	let n = W(null), r = W(t);
	return r.current = t, U(() => {
		let t = n.current;
		t.innerHTML = l([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = p(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ G("div", {
		ref: n,
		class: "scraping-network"
	});
}
function dn({ source: e, toast: t }) {
	let [n, r] = V(e), [i, o] = V(e.network), [c, l] = V(""), [u, f] = V(""), [p, m] = V("paste"), [h, g] = V(""), [_, v] = V(!1), [y, b] = V(""), [x, S] = V([]), C = W(null), w = W(null);
	U(() => {
		w.current?.querySelectorAll("footer button").forEach((e) => d(e, _));
	}, [_]);
	let T = W(new AbortController());
	H(() => () => T.current.abort(), []);
	async function E(n) {
		if (!_) {
			v(!0), b(""), S([]);
			try {
				if (n === "check") {
					let t = await L("/api/scraping/check", { source: e.source }, "POST", T.current.signal);
					T.current.signal.aborted || S(t.results);
				} else {
					let a = await L("/api/scraping/settings", {
						source: e.source,
						network: i,
						cookie: c,
						cookies_text: u,
						revoke: n === "revoke"
					}, "POST", T.current.signal);
					T.current.signal.aborted || (r(a.saved), l(""), f(""), g(""), C.current && (C.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				T.current.signal.aborted || b(F(e));
			} finally {
				T.current.signal.aborted || v(!1);
			}
		}
	}
	return /* @__PURE__ */ G("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ G("form", {
			ref: w,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), E("save");
			},
			children: [/* @__PURE__ */ G("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ G("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: e.login
					}),
					/* @__PURE__ */ G("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ G(un, {
							value: i,
							onChange: o
						})]
					}),
					i === "peach" && /* @__PURE__ */ G("a", {
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ G(N, { children: [
						/* @__PURE__ */ G("p", { children: n.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ G("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ G("label", { children: [/* @__PURE__ */ G("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: p === t,
								onChange: () => {
									m(t), l(""), f(""), g("");
								}
							}), /* @__PURE__ */ G("span", { children: n })] }, t))
						}),
						p === "paste" ? /* @__PURE__ */ G("label", { children: ["Cookie", /* @__PURE__ */ G("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: c,
							disabled: _,
							onInput: (e) => l(e.currentTarget.value)
						})] }) : /* @__PURE__ */ G("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ G("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ G("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ G("span", {
										class: "scraping-file-name",
										children: h || "未选择文件"
									}),
									/* @__PURE__ */ G("input", {
										ref: C,
										type: "file",
										accept: ".txt",
										disabled: _,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												f(""), g("");
												return;
											}
											if (f(""), t.size > 262144) {
												b("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											v(!0);
											try {
												let e = await t.text();
												T.current.signal.aborted || (f(e), g(t.name));
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
					y && /* @__PURE__ */ G("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: s(y, { variant: "error" }) }
					}),
					x.map((t) => /* @__PURE__ */ G("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: s(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ G("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ G("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ G("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void E("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ G("button", {
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
function fn({ data: e, error: t, toast: n }) {
	let [r, i] = V(""), [o, c] = V(!1), [l, u] = V(""), f = W(null);
	U(() => d(f.current, o), [o]);
	let p = W(new AbortController()), m = W(0);
	async function h(e = !1) {
		let t = ++m.current;
		await sn({
			read: (e) => I("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				c(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && u(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => u("连接中断，正在重新读取后台进度")
		});
	}
	H(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!o) {
			m.current++, c(!0), u("");
			try {
				await L("/api/scraping/cover", { code: r }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (c(!1), u(F(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ G("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: s(t, { variant: "error" }) }
	}) : /* @__PURE__ */ G("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ G("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ G("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ G("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ G("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ G("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: o,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => i(e.currentTarget.value)
							}), /* @__PURE__ */ G("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						l && /* @__PURE__ */ G("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: s(l, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ G(dn, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var pn = (e, t) => I("/api/library-processing", t);
function mn({ data: e, error: t, toast: n, onComplete: r, mode: i, monitor: l }) {
	let [u, f] = V(e || { status: "idle" }), [p, m] = V(t), [h, g] = V(!1), [_, v] = V(!1), y = W(new AbortController()), b = W(0), x = W(u.status), S = W(null), C = h || u.status === "running";
	U(() => d(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await sn({
			read: (e) => I("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: i === "notice" || !!l,
			render: (e) => {
				f(e), m(""), e.status === "complete" && x.current === "running" && i !== "notice" && (v(!0), n("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => m("连接中断，正在重新读取处理进度")
		});
	}
	H(() => ((u.status === "running" || i === "notice" || l) && w(), () => y.current.abort()), []);
	async function T() {
		if (!C) {
			g(!0), m(""), v(!1);
			try {
				let e = await L("/api/library-processing", {}, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = e.status, f(e), g(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (m(F(e)), g(!1));
			}
		}
	}
	return i === "notice" ? !p && u.status !== "running" && u.status !== "failed" ? null : /* @__PURE__ */ G("div", {
		class: "library-processing-banner",
		role: "status",
		children: [/* @__PURE__ */ G("span", { children: p || (u.status === "failed" ? "扫描与资料采集未完成" : `${u.stage || "正在整理馆藏"}${u.total ? ` · ${u.checked || 0} / ${u.total}` : ""}`) }), /* @__PURE__ */ G("a", {
			class: "geist-button",
			href: "/data-cleanup#libraryProcessing",
			children: p || u.status === "failed" ? "查看并处理" : "查看进度"
		})]
	}) : /* @__PURE__ */ G(N, { children: [/* @__PURE__ */ G("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: a("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ G("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ G("div", {
				"aria-live": "polite",
				children: [
					u.status === "running" && /* @__PURE__ */ G(N, { children: [/* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: o(`${u.stage || "正在处理"}${u.total ? ` · ${u.checked || 0} / ${u.total}` : ""}`) } }), !!u.total && /* @__PURE__ */ G("div", { dangerouslySetInnerHTML: { __html: c(`已处理 ${u.checked || 0} / ${u.total} 个视频`, u.checked || 0, u.total) } })] }),
					(p || u.status === "failed") && /* @__PURE__ */ G("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: s(p || u.error || "处理未完成，请重试", { variant: "error" }) }
					}),
					u.status === "failed" && !!u.issues?.length && /* @__PURE__ */ G("ul", { children: u.issues.slice(0, 20).map((e) => /* @__PURE__ */ G("li", { children: [
						e.asset_id ? /* @__PURE__ */ G("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					_ && /* @__PURE__ */ G("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: s(`已扫描 ${u.scanned || 0} 个文件，识别 ${u.identified || 0} 个番号，整理 ${u.candidates || 0} 组资料候选。`, {
							variant: "success",
							label: "处理完成"
						}) }
					})
				]
			})
		]
	}), /* @__PURE__ */ G("footer", {
		class: "geist-fieldset-footer",
		"data-geist-fieldset-footer": !0,
		children: [
			/* @__PURE__ */ G("a", {
				class: "geist-button",
				href: "/scraping",
				children: "采集来源"
			}),
			!!u.candidates && /* @__PURE__ */ G("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			/* @__PURE__ */ G("button", {
				ref: S,
				type: "button",
				class: "geist-button primary",
				onClick: () => void T(),
				children: u.status === "failed" ? "重试未完成项" : "扫描并补全资料"
			})
		]
	})] });
}
//#endregion
//#region src/state/index.ts
var hn = { "quality-goals": {
	refresh: nn,
	reset: tn
} }, gn = () => Object.keys(hn);
async function _n(e) {
	let t = hn[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-bulk.ts
var vn = () => ({
	busy: !1,
	groupBy: "candidates",
	anchor: null,
	selected: /* @__PURE__ */ new Set(),
	choices: /* @__PURE__ */ new Map(),
	assets: /* @__PURE__ */ new Map(),
	errors: /* @__PURE__ */ new Map()
});
function yn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r of e) {
		let e, i;
		if (t === "field") e = r.field || "", i = r.field_label || r.field || "未标注字段";
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
function bn(e, t, n, r, i) {
	let a = e.anchor === null ? -1 : t.indexOf(e.anchor), o = t.indexOf(n);
	r && a >= 0 && o >= 0 ? t.slice(Math.min(a, o), Math.max(a, o) + 1).forEach((t) => e.selected.add(t)) : i ? e.selected.add(n) : e.selected.delete(n), e.anchor = n;
}
async function xn(e, t, n, r) {
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
				message: F(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function Sn(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Cn(e, r) {
	let i = e.querySelector(".reviewlist");
	if (!i || !r.rows.length || r.locked) return;
	let a = r.state, o = [...i.querySelectorAll("[data-review-key]")], s = () => [...i.querySelectorAll("[data-review-key]")], c = () => s().filter((e) => a.selected.has(e.dataset.reviewKey)), u = () => r.rows.filter((e) => a.selected.has(e.item_key)), f = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, m = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, h = document.createElement("div");
	h.className = "reviewbulkbar reviewbulktoolbar", h.setAttribute("role", "group"), h.setAttribute("aria-label", "复核批量操作");
	let g = document.createElement("div");
	g.className = "reviewgroupby", g.innerHTML = l([
		["candidates", "按候选数量"],
		["source", "按来源"],
		["field", "按字段"]
	], a.groupBy, { label: "分组方式" });
	let _ = p(g.firstElementChild);
	_.addEventListener("change", () => {
		if (a.busy || ![
			"candidates",
			"source",
			"field"
		].includes(_.value)) return;
		a.groupBy = _.value, a.anchor = null;
		let t = e.parentElement;
		r.refresh(), t?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let v = m("全选本页"), y = m("通过所选", "primary"), b = m("拒绝所选", "error"), x = document.createElement("span");
	x.className = "reviewselectedcount", x.setAttribute("role", "status");
	let S = document.createElement("div");
	S.className = "reviewbulksource", S.hidden = !r.metadata;
	let C = document.createElement("p");
	C.className = "reviewstate reviewbulkfeedback", C.setAttribute("role", "status");
	let w = document.createElement("div");
	w.className = "reviewbulkdecisions", w.append(y, b), h.append(g, v, x, S, w), i.before(h, C), i.classList.add("reviewgroups");
	let T = () => {
		a.selected.clear(), a.anchor = null, O();
	};
	v.onclick = () => {
		a.busy || (c().length === o.length ? T() : (o.forEach((e) => a.selected.add(e.dataset.reviewKey)), O()));
	}, y.onclick = () => k("approved", y), b.onclick = () => k("rejected", b);
	let E = [];
	for (let e of yn(r.rows, a.groupBy)) {
		let t = e.rows.map((e) => o.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e), r = document.createElement("section");
		r.className = "reviewgroup";
		let c = document.createElement("div");
		c.className = "reviewbulkbar";
		let l = document.createElement("h3");
		l.textContent = `${e.title} · ${t.length}`;
		let u = m("全选本组"), d = document.createElement("div");
		d.className = "reviewlist", c.append(l, u), r.append(c, d), i.append(r), u.onclick = () => {
			if (a.busy) return;
			let e = t.every((e) => a.selected.has(e.dataset.reviewKey));
			t.forEach((t) => e ? a.selected.delete(t.dataset.reviewKey) : a.selected.add(t.dataset.reviewKey)), O();
		}, E.push(() => {
			u.textContent = t.every((e) => a.selected.has(e.dataset.reviewKey)) ? "清空本组" : "全选本组";
		});
		for (let e of t) {
			d.append(e);
			let t = e.dataset.reviewKey;
			a.errors.has(t) && (e.querySelector(".reviewstate").textContent = a.errors.get(t));
			let r = e.querySelector("h4,.reviewentity b") || e, i = document.createElement("label");
			i.className = "reviewpickitem", i.innerHTML = n();
			let o = i.querySelector("input");
			if (o.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || r.textContent || t}`), r !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...r.childNodes), r.classList.add("reviewpickheading"), r.append(i, e);
			} else e.prepend(i);
			let c = (e, n) => {
				bn(a, s().map((e) => e.dataset.reviewKey), t, e, n), O();
			};
			if (i.addEventListener("click", (e) => {
				e.target !== o && (e.preventDefault(), a.busy || (o.focus(), c(e.shiftKey, !o.checked)));
			}), o.addEventListener("click", (e) => {
				a.busy || c(e.shiftKey, o.checked);
			}), o.addEventListener("keydown", (n) => {
				if (!(a.busy || !n.shiftKey)) {
					if (n.key === " ") n.preventDefault(), c(!0, !0);
					else if (n.key === "ArrowDown" || n.key === "ArrowUp") {
						n.preventDefault();
						let r = s(), i = r[r.indexOf(e) + (n.key === "ArrowDown" ? 1 : -1)];
						i && (a.anchor === null && (a.anchor = t), bn(a, r.map((e) => e.dataset.reviewKey), i.dataset.reviewKey, !0, !0), O(), i.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), E.push(() => {
				o.checked = a.selected.has(t);
			}), a.assets.has(t)) {
				let n = a.assets.get(t), r = [...e.querySelectorAll("[data-review-asset]")];
				r.forEach((e) => {
					let t = n.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(t)), e.classList.toggle("picked", t);
				});
				let i = e.querySelector("[data-picked-count]");
				i && (i.textContent = `已选 ${n.length} / ${r.length}`);
			}
			e.addEventListener("click", (n) => {
				n.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && a.assets.set(t, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let n of e.querySelectorAll("input[type=\"radio\"]")) a.choices.has(t) && (n.checked = a.choices.get(t) === n.value), n.addEventListener("change", () => {
				n.checked && a.choices.set(t, n.value), O();
			});
		}
	}
	e.addEventListener("keydown", (e) => {
		a.busy || (e.key === "Escape" && a.selected.size && (e.preventDefault(), e.stopPropagation(), T()), (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "a" && !e.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (e.preventDefault(), e.stopPropagation(), o.forEach((e) => a.selected.add(e.dataset.reviewKey)), O()));
	});
	let D = "";
	function O() {
		let e = c();
		v.textContent = e.length === o.length ? "清空选择" : "全选本页", x.innerHTML = t(`已选 ${e.length} 项`), y.disabled = !e.length || e.some((e) => !f(e)), b.disabled = !e.length;
		let n = Sn(u()), i = e.length && !n.length ? "所选项目无共同来源" : "统一选择来源", s = JSON.stringify([i, n]);
		if (s !== D) {
			D = s, S.innerHTML = l([["", i], ...n.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = p(S.firstElementChild);
			e.disabled = !n.length, e.addEventListener("change", () => {
				if (!(a.busy || !Sn(u()).includes(e.value))) {
					for (let t of c()) {
						let n = r.rows.find((e) => e.item_key === t.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						t.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === n.candidate_key;
						}), a.choices.set(t.dataset.reviewKey, n.candidate_key);
					}
					C.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		E.forEach((e) => e());
	}
	async function k(t, n) {
		if (a.busy || !c().length) return;
		let i = c().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...r.payload(e),
				status: t
			}
		}));
		if (t === "approved" && r.metadata && i.some((e) => !e.payload.candidate_key)) {
			C.textContent = "请先为所选的多来源候选选择来源。", c().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		a.busy = !0, C.textContent = `正在处理 0 / ${i.length}`, d(n, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let l = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", l, !0), e.addEventListener("keydown", l, !0);
		let u = 0, f = await xn(i, async (e) => {
			try {
				return await r.submit(e);
			} finally {
				u++, r.active() && (C.textContent = `正在处理 ${u} / ${i.length}`);
			}
		}, (e) => {
			a.selected.delete(e), a.errors.delete(e), r.applied(e);
		}, r.active);
		if (a.busy = !1, e.removeEventListener("click", l, !0), e.removeEventListener("keydown", l, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), d(n, !1), !r.active()) return;
		r.notify(`已${t === "approved" ? "通过" : "拒绝"} ${f.completed} 项${f.failures.length ? `，${f.failures.length} 项未完成` : ""}`), f.failures.forEach((e) => a.errors.set(e.key, e.message));
		let p = e.parentElement;
		r.refresh(), p?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	O();
}
//#endregion
//#region src/native-image.ts
function wn(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function Tn(e, t, n, r, i = 1) {
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
function En(e, t) {
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
var Dn = [
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
function On() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function kn(e, t) {
	let n = new URLSearchParams();
	for (let t of Dn) e[t] && n.set(t, e[t]);
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
function An({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: r = !1, online: a = !1 } = {}) {
	let o = r ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", s = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	return t || n ? i("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" }) : e === "catalog" ? i("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s }) : i(e === "tags" ? "tags" : "user-round", "还没有" + ({
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
function jn(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Mn(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Nn(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function Pn(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function Fn(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function In() {
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
function Ln(e, t = !1, n = !1) {
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
var Rn = "peach-taste-guide-dismissed";
function zn(e, t) {
	f(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Rn, "1"), n.remove();
	});
}
//#endregion
//#region src/jav-artwork.ts
function Bn(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function Vn(e) {
	return {
		javLayout: Bn(e.javLayout),
		javImage: Hn(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Hn(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Un(e, t) {
	return e.is_jav && e.code && e.has_cover && (Hn(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Wn(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Hn(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var Gn = {
	"library-processing": {
		load: pn,
		component: mn
	},
	scraping: {
		load: ln,
		component: fn
	},
	"quality-goals": {
		load: rn,
		component: on
	},
	configuration: {
		load: dt,
		component: _t
	}
}, Kn = () => Object.keys(Gn), $ = /* @__PURE__ */ new Map();
async function qn(e, t, n, r = {}) {
	let i = Gn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Jn(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	$.set(t, a);
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
			error: F(e)
		};
	}
	if ($.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		$.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	Oe(oe(i.component, s), t);
}
function Jn(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.painted && Oe(null, e));
}
//#endregion
export { Rn as TASTE_GUIDE_KEY, An as catalogEmptyHtml, kn as catalogSuggestions, In as cleanupSkeletonHtml, Pn as cloudLocations, Fn as cloudPreferenceLocations, vn as createReviewSelection, On as emptyCatalogLayout, En as entitySkeletonHtml, cn as followJobProgress, Kn as islandNames, Un as javImageKind, wn as matchesFaceSource, qn as mountIsland, Tn as nativeImageFit, Hn as normalizeJavImage, Bn as normalizeJavLayout, Vn as normalizeJavPreferences, ke as preferredDirection, _n as refreshStore, jn as sidebarHasCatalogContent, Nn as sidebarTagCounts, gn as storeNames, Wn as syncJavImages, Mn as syncSidebarSurface, Ln as tasteHistoryGuideHtml, Jn as unmountIsland, sn as watchJob, Cn as wireReviewSelection, zn as wireTasteHistoryGuide };
