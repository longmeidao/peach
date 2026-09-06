import { MEDIA_SOURCE_ICONS as e, checkboxHtml as t, confirmModal as n, emptyStateHtml as r, fieldsetTitle as i, loadingDotsHtml as a, noteHtml as o, progressHtml as s, selectFieldHtml as c, selectOptionIconHtml as l, setActionBusy as u, wireCollapse as d, wireSelectField as f } from "/js/ui-components.js";
import { LOC as p, faviconUrl as m, fmtDur as h, fmtSize as g, icon as _ } from "/js/core.js";
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
function P(e, t) {
	this.props = e, this.context = t;
}
function F(e, t) {
	if (t == null) return e.__ ? F(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? F(e) : null;
}
function ce(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = M({}, t);
		a.__v = t.__v + 1, y.vnode && y.vnode(a), ye(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? F(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, xe(r, a, i), t.__e = t.__ = null, a.__e != n && le(a);
	}
}
function le(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), le(e);
}
function ue(e) {
	(!e.__d && (e.__d = !0) && S.push(e) && !de.__r++ || C != y.debounceRendering) && ((C = y.debounceRendering) || w)(de);
}
function de() {
	try {
		for (var e, t = 1; S.length;) S.length > t && S.sort(T), e = S.shift(), t = S.length, ce(e);
	} finally {
		S.length = de.__r = 0;
	}
}
function fe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || ne, v = t.length;
	for (c = pe(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || j, p.__i = d, g = ye(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && we(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = me(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function pe(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = se(null, o, null, null, null) : ie(o) ? o = e.__k[a] = se(N, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = se(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = he(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = F(s)), Te(s, s));
	return r;
}
function me(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = me(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = F(e)), t = n.insertBefore(e.__e, t || null));
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
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || re.test(t) ? n : n + "px";
}
function _e(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ge(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ge(e.style, t, n[t]);
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
function ve(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[D] == null) t[D] = A++;
			else if (t[D] < n[O]) return;
			return n(y.event ? y.event(t) : t);
		}
	};
}
function ye(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, g, _, v, b, x, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = y.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (v = t.props, b = D.prototype && D.prototype.render, x = (u = D.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? _ = (f = t.__c = n.__c).__ = f.__E : (b ? t.__c = f = new D(v, S) : (t.__c = f = new P(v, S), f.constructor = D, f.render = Ee), x && x.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), b && f.__s == null && (f.__s = f.state), b && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = M({}, f.__s)), M(f.__s, D.getDerivedStateFromProps(v, f.__s))), m = f.props, h = f.state, f.__v = t, p) b && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), b && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (b && D.getDerivedStateFromProps == null && v !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(v, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(v, f.__s, S)) {
					t.__v != n.__v && (f.props = v, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), ne.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = F(n);
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
			f.state = f.__s, f.getChildContext != null && (r = M(M({}, r), f.getChildContext())), b && !p && f.getSnapshotBeforeUpdate != null && (g = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === N && u.key == null ? Se(u.props.children) : u, s = fe(e, ie(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), _ && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ae(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || be(t), y.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = Ce(n.__e, t, n, r, i, a, o, c, l);
	return (u = y.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function be(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(be));
}
function xe(e, t, n) {
	for (var r = 0; r < n.length; r++) we(n[r], n[++r], n[++r]);
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
function Se(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : ie(e) ? e.map(Se) : e.constructor === void 0 ? M({}, e) : null;
}
function Ce(e, t, n, r, i, a, o, s, c) {
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
		for (l in g) p = g[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in _ || l == "value" && "defaultValue" in _ || l == "checked" && "defaultChecked" in _ || _e(e, l, null, p, i);
		for (l in _) p = _[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? h = p : s && typeof p != "function" || g[l] === p || _e(e, l, p, g[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), fe(t.type == "template" ? e.content : e, ie(f) ? f : [f], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && F(n, 0), s, c), a != null) for (l = a.length; l--;) ae(a[l]);
		s && b != "textarea" || (l = "value", b == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || b == "progress" && !m || b == "option" && m != g[l]) && _e(e, l, m, g[l], i), l = "checked", h != null && h != e[l] && _e(e, l, h, g[l], i));
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
		y.__e(e, n);
	}
}
function Te(e, t, n) {
	var r, i;
	if (y.unmount && y.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || we(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			y.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && Te(r[i], t, n || typeof e.type != "function");
	n || ae(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Ee(e, t, n) {
	return this.constructor(e, n);
}
function De(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), y.__ && y.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], ye(t, e = (!r && n || t).__k = oe(N, null, [e]), i || j, j, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? v.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), xe(a, e, o), e.props.children = null;
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
}, P.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = M({}, this.state);
	typeof e == "function" && (e = e(M({}, n), this.props)), e && M(n, e), e != null && this.__v && (t && this._sb.push(t), ue(this));
}, P.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ue(this));
}, P.prototype.render = N, S = [], w = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, T = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, de.__r = 0, E = Math.random().toString(8), D = "__d" + E, O = "__a" + E, k = /(PointerCapture)$|Capture$/i, A = 0, ee = ve(!1), te = ve(!0);
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
		super(e), this.name = "ApiError", this.status = t, this.body = n;
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
}, I = (e) => e instanceof Error ? e.message : String(e);
async function L(e, t) {
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
async function R(e, t, n = "POST", r) {
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
var z, B, je, Me, Ne = 0, Pe = [], V = y, Fe = V.__b, Ie = V.__r, Le = V.diffed, Re = V.__c, ze = V.unmount, Be = V.__;
function Ve(e, t) {
	V.__h && V.__h(B, e, Ne || t), Ne = 0;
	var n = B.__H || (B.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function H(e) {
	return Ne = 1, He(Xe, e);
}
function He(e, t, n) {
	var r = Ve(z++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Xe(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = B, !B.__f)) {
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
		B.__f = !0;
		var a = B.shouldComponentUpdate, o = B.componentWillUpdate;
		B.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, B.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function U(e, t) {
	var n = Ve(z++, 3);
	!V.__s && Ye(n.__H, t) && (n.__ = e, n.u = t, B.__H.__h.push(n));
}
function W(e, t) {
	var n = Ve(z++, 4);
	!V.__s && Ye(n.__H, t) && (n.__ = e, n.u = t, B.__h.push(n));
}
function G(e) {
	return Ne = 5, Ue(function() {
		return { current: e };
	}, []);
}
function Ue(e, t) {
	var n = Ve(z++, 7);
	return Ye(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function We() {
	for (var e; e = Pe.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(qe), t.__h.some(Je), t.__h = [];
		} catch (n) {
			t.__h = [], V.__e(n, e.__v);
		}
	}
}
V.__b = function(e) {
	B = null, Fe && Fe(e);
}, V.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Be && Be(e, t);
}, V.__r = function(e) {
	Ie && Ie(e), z = 0;
	var t = (B = e.__c).__H;
	t && (je === B ? (t.__h = [], B.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(qe), t.__h.some(Je), t.__h = [], z = 0)), je = B;
}, V.diffed = function(e) {
	Le && Le(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Pe.push(t) !== 1 && Me === V.requestAnimationFrame || ((Me = V.requestAnimationFrame) || Ke)(We)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), je = B = null;
}, V.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(qe), e.__h = e.__h.filter(function(e) {
				return !e.__ || Je(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], V.__e(n, e.__v);
		}
	}), Re && Re(e, t);
}, V.unmount = function(e) {
	ze && ze(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			qe(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && V.__e(t, n.__v));
};
var Ge = typeof requestAnimationFrame == "function";
function Ke(e) {
	var t, n = function() {
		clearTimeout(r), Ge && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Ge && (t = requestAnimationFrame(n));
}
function qe(e) {
	var t = B, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), B = t;
}
function Je(e) {
	var t = B;
	e.__c = e.__(), B = t;
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
function K(e, t, n, r, i, a) {
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
	return y.vnode && y.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function Qe({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1 }) {
	return /* @__PURE__ */ K("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ K("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ K("input", {
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
			i || a ? /* @__PURE__ */ K("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function $e({ initial: e, receipt: t }) {
	let [n, r] = H(e), [a, o] = H(""), [s, c] = H(""), [l, d] = H(""), [f, p] = H(!1), [m, h] = H(""), [g, _] = H({}), v = G(null), y = G(!1), b = G(null);
	return /* @__PURE__ */ K("form", {
		class: "configfieldset",
		onSubmit: async (e) => {
			if (e.preventDefault(), y.current) return;
			h("");
			let i = {};
			if (n.mode === "password" && !a && (i.current_password = "请输入当前访问密码"), f || ((s.length < 8 || s.length > 256) && (i.password = "访问密码需为 8–256 个字符"), s !== l && (i.confirmation = "两次输入的密码不一致")), _(i), Object.keys(i).length) {
				requestAnimationFrame(() => v.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			y.current = !0, u(b.current, !0);
			try {
				let e = await R("/api/configuration/access", {
					revision: n.revision,
					action: f ? "disable" : "set",
					confirm_disable: f,
					current_password: a,
					password: f ? "" : s,
					confirmation: f ? "" : l
				});
				r(e), o(""), c(""), d(""), p(!1), _({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof ke ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? _(n) : h(I(e));
			} finally {
				y.current = !1, u(b.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: v,
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("accessTitle", "访问密码") } }), /* @__PURE__ */ K("p", {
						class: "confighelp",
						children: n.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : n.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : n.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
					})]
				}),
				n.mode === "password" ? /* @__PURE__ */ K(Qe, {
					id: "access-current",
					label: "当前访问密码",
					value: a,
					onInput: o,
					error: g.current_password,
					current: !0
				}) : null,
				!f && n.mode !== "locked" ? /* @__PURE__ */ K(N, { children: [/* @__PURE__ */ K(Qe, {
					id: "access-password",
					label: n.mode === "password" ? "新访问密码" : "设置访问密码",
					value: s,
					onInput: c,
					error: g.password,
					help: "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ K(Qe, {
					id: "access-confirm",
					label: "确认访问密码",
					value: l,
					onInput: d,
					error: g.confirmation
				})] }) : null,
				n.mode === "password" || n.mode === "legacy" ? /* @__PURE__ */ K("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ K("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ K("input", {
							type: "checkbox",
							checked: f,
							onChange: (e) => p(e.currentTarget.checked)
						}), /* @__PURE__ */ K("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ K("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ K("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ K("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				m ? /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: m
				}) : null
			]
		}), n.mode === "locked" ? null : /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ K("p", { children: "保存后立即生效。" }), /* @__PURE__ */ K("button", {
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
var et = /* @__PURE__ */ new Set([
	"downloading",
	"verifying",
	"extracting",
	"preparing",
	"restarting",
	"installing"
]);
function tt({ initial: e, initialJob: t }) {
	let [r, a] = H(e), [o, c] = H(t || {
		state: "idle",
		progress: 0
	}), [l, d] = H(""), f = G(null), p = G(!0), m = G(!1), h = G(null);
	U(() => {
		u(h.current, et.has(o.state));
	}, [o.state]), U(() => () => {
		p.current = !1, f.current?.abort();
	}, []);
	let g = async () => {
		let e = await R("/api/configuration/update-restart", {});
		p.current && c(e);
	};
	U(() => {
		o.state !== "ready" || m.current || (m.current = !0, n({
			title: "更新已准备好",
			body: `Peach ${o.version || ""} 将在重启后安装。`,
			confirmLabel: "立即重启",
			cancelLabel: "稍后",
			onConfirm: g
		}));
	}, [o.state]), U(() => {
		if (!et.has(o.state)) return;
		let e = new AbortController(), t, n = 0, r = async () => {
			try {
				let t = await L("/api/configuration/update-status", e.signal);
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
		if (f.current || et.has(o.state)) return;
		let t = new AbortController();
		f.current = t, m.current = !1, d(""), u(e, !0);
		try {
			let e = await R("/api/configuration/update", {}, "POST", t.signal);
			t.signal.aborted || c(e);
		} catch (e) {
			t.signal.aborted || d(I(e));
		} finally {
			f.current = null, u(e, !1);
		}
	}, v = async (t) => {
		if (f.current) return;
		let n = new AbortController();
		f.current = n, u(t, !0), d("");
		try {
			let e = await L("/api/configuration/updates", n.signal);
			n.signal.aborted || a(e);
		} catch (t) {
			n.signal.aborted || (a({
				...e,
				state: "error"
			}), d(I(t)));
		} finally {
			f.current = null, u(t, !1);
		}
	};
	return /* @__PURE__ */ K("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configUpdatesTitle",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("configUpdatesTitle", "检查更新") } }),
				/* @__PURE__ */ K("dl", {
					class: "configfacts",
					children: [
						/* @__PURE__ */ K("dt", { children: "当前版本" }),
						/* @__PURE__ */ K("dd", { children: r.current_version }),
						/* @__PURE__ */ K("dt", { children: "安装方式" }),
						/* @__PURE__ */ K("dd", { children: r.installation }),
						/* @__PURE__ */ K("dt", { children: "更新通道" }),
						/* @__PURE__ */ K("dd", { children: r.channel }),
						/* @__PURE__ */ K("dt", { children: "最新版本" }),
						/* @__PURE__ */ K("dd", { children: r.latest_version || (r.state === "unchecked" ? "尚未检查" : "未取得") })
					]
				}),
				/* @__PURE__ */ K("p", {
					class: l || r.state === "error" ? "configbad" : "confighelp",
					role: l || r.state === "error" ? "alert" : "status",
					children: l || r.message
				}),
				o.state === "idle" ? null : /* @__PURE__ */ K("div", {
					"aria-live": "polite",
					children: [/* @__PURE__ */ K("p", {
						class: o.state === "error" ? "configbad" : "confighelp",
						children: o.message
					}), o.state === "error" ? null : /* @__PURE__ */ K(N, { children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: s(o.state === "downloading" ? "下载进度" : "安装进度", o.state === "downloading" ? o.downloaded || 0 : o.progress, o.state === "downloading" ? o.total || 1 : 100) } }), /* @__PURE__ */ K("p", {
						class: "confighelp",
						children: o.state === "downloading" && o.total ? `${((o.downloaded || 0) / 1048576).toFixed(1)} / ${(o.total / 1048576).toFixed(1)} MB` : `${o.progress}%`
					})] })]
				})
			]
		}), /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [
				/* @__PURE__ */ K("a", {
					class: "geist-button",
					href: r.release_url,
					target: "_blank",
					rel: "noreferrer",
					children: "查看发布页"
				}),
				o.state === "ready" ? /* @__PURE__ */ K("button", {
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
				r.state === "available" && r.installation === "独立测试包" && o.state !== "ready" ? /* @__PURE__ */ K("button", {
					ref: h,
					type: "button",
					class: "geist-button primary",
					onClick: (e) => _(e.currentTarget),
					children: "下载并安装"
				}) : null,
				/* @__PURE__ */ K("button", {
					type: "button",
					class: "geist-button",
					disabled: et.has(o.state),
					onClick: (e) => v(e.currentTarget),
					children: "检查更新"
				})
			]
		})]
	});
}
//#endregion
//#region src/islands/peach-proxy.tsx
function nt({ initial: e, receipt: t }) {
	let [n, r] = H(e), [a, o] = H(e.mode), [s, l] = H(""), [d, p] = H(""), m = G(!1), h = G(null), g = G(null), _ = G(new AbortController());
	U(() => () => _.current.abort(), []), W(() => {
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
				let e = await R("/api/configuration/peach-proxy", {
					mode: a,
					proxy: s
				}, "POST", _.current.signal);
				_.current.signal.aborted || (r(e), l(""), t("已保存 Peach 代理"));
			} catch (e) {
				_.current.signal.aborted || p(I(e));
			} finally {
				m.current = !1, u(g.current, !1);
			}
		}
	}
	return /* @__PURE__ */ K("form", {
		id: "peachProxy",
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), v();
		},
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("peachProxyTitle", "Peach 代理") } }),
				/* @__PURE__ */ K("p", {
					class: "confighelp",
					children: "采集来源选择“Peach 代理”时共用此设置。"
				}),
				/* @__PURE__ */ K("div", { ref: h }),
				a === "proxy" && /* @__PURE__ */ K("div", {
					class: "configfield",
					children: [/* @__PURE__ */ K("label", {
						htmlFor: "peachProxyAddress",
						children: "代理地址"
					}), /* @__PURE__ */ K("input", {
						id: "peachProxyAddress",
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: s,
						placeholder: n.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						onInput: (e) => l(e.currentTarget.value)
					})]
				}),
				n.needs_selection && /* @__PURE__ */ K("p", {
					class: "configbad",
					children: "已有来源的代理地址不同，请选择公共连接方式。"
				}),
				d && /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: d
				})
			]
		}), /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ K("button", {
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
function rt({ label: e, checked: t, disabled: n, change: r }) {
	return /* @__PURE__ */ K("label", {
		class: "configcheck",
		children: [/* @__PURE__ */ K("span", {
			class: "pcheck",
			children: [/* @__PURE__ */ K("input", {
				type: "checkbox",
				checked: t,
				disabled: n,
				onChange: (e) => r(e.currentTarget.checked)
			}), /* @__PURE__ */ K("span", {
				"aria-hidden": "true",
				children: /* @__PURE__ */ K("svg", {
					viewBox: "0 0 24 24",
					children: /* @__PURE__ */ K("use", { href: "#i-check" })
				})
			})]
		}), /* @__PURE__ */ K("span", { children: e })]
	});
}
function it({ startup: e, receipt: t }) {
	let [n, r] = H(e.enabled), [a, o] = H(e.silent), [s, c] = H(""), l = G(!1), d = G(null);
	async function f() {
		if (!l.current) {
			l.current = !0, u(d.current, !0), c("");
			try {
				await R("/api/configuration/startup", {
					enabled: n,
					silent: a
				}), t("已保存开机自启");
			} catch (e) {
				c(I(e));
			} finally {
				l.current = !1, u(d.current, !1);
			}
		}
	}
	return /* @__PURE__ */ K("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		onSubmit: (e) => {
			e.preventDefault(), f();
		},
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("startupTitle", "开机自启") } }),
				/* @__PURE__ */ K(rt, {
					label: "开机后启动 Peach",
					checked: n,
					disabled: !e.available,
					change: r
				}),
				/* @__PURE__ */ K(rt, {
					label: "静默启动",
					checked: a,
					disabled: !e.available,
					change: o
				}),
				/* @__PURE__ */ K("p", {
					class: "confighelp",
					children: "静默启动仅显示托盘；关闭后自动打开浏览器。"
				}),
				e.message && /* @__PURE__ */ K("p", {
					class: "confighelp",
					children: e.message
				}),
				s && /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: s
				})
			]
		}), /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ K("button", {
				ref: d,
				type: "submit",
				class: "geist-button primary",
				disabled: !e.available,
				children: "保存自启"
			})
		})]
	});
}
function at({ data: e }) {
	let t = G(null);
	return W(() => {
		let n = t.current, r = document.createElement("details");
		r.className = "configdirectories";
		let i = document.createElement("summary");
		i.innerHTML = _("chevron-right") + "<span>数据目录</span>", r.append(i);
		for (let t of [.../* @__PURE__ */ new Set([e.data_root, ...e.directories])]) {
			let e = document.createElement("p");
			e.className = "confighelp", e.textContent = t, r.append(e);
		}
		return n.replaceChildren(r), d(n, "details", "uninstall-data"), () => n.replaceChildren();
	}, [e]), /* @__PURE__ */ K("div", { ref: t });
}
function ot({ uninstall: e }) {
	let [t, r] = H(!1), [a, o] = H("");
	async function s() {
		await n({
			title: "卸载 Peach",
			danger: !0,
			body: t ? "将退出 Peach，移除程序、开机自启、设置、本地数据库、观看记录、凭据和缓存。原始媒体文件保留。" : "将退出 Peach 并移除程序和开机自启。设置、本地数据库、观看记录与缓存保留。",
			confirmLabel: "卸载 Peach",
			onConfirm: async () => {
				let e = await R("/api/configuration/uninstall", {
					delete_data: t,
					confirmation: "卸载 Peach"
				});
				o(e.message);
			}
		});
	}
	return /* @__PURE__ */ K("section", {
		id: "uninstallPeach",
		class: "configfieldset configdanger",
		"data-geist-fieldset": !0,
		"data-fieldset-type": "error",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("uninstallTitle", "卸载 Peach") } }),
				e.available && /* @__PURE__ */ K("p", {
					class: "confighelp",
					children: "卸载会退出 Peach、移除程序和开机自启。原始媒体文件保留。"
				}),
				/* @__PURE__ */ K(rt, {
					label: "完全卸载：同时删除设置、本地数据库、观看记录、凭据和缓存",
					checked: t,
					disabled: !e.full_available || !!a,
					change: r
				}),
				/* @__PURE__ */ K(at, { data: e }),
				e.message && /* @__PURE__ */ K("p", {
					class: "confighelp",
					children: e.message
				}),
				a && /* @__PURE__ */ K("p", {
					class: "confighelp",
					role: "status",
					children: a
				})
			]
		}), /* @__PURE__ */ K("footer", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ K("button", {
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
var st = "/api/configuration", ct = "/api/pick-folder", lt = 8e3, ut = (e, t) => L(st, t), q = ({ html: e, class: t }) => /* @__PURE__ */ K("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), dt = (e) => !(e instanceof ke) || e.status !== 400 ? null : e.body?.errors ?? null;
function ft({ facts: e }) {
	return /* @__PURE__ */ K("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ K(q, { html: i("configFactsTitle", "运行信息") }), /* @__PURE__ */ K("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ K(N, { children: [/* @__PURE__ */ K("dt", { children: e.term }), /* @__PURE__ */ K("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ K("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ K("a", {
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ K("svg", {
							"aria-hidden": "true",
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function pt({ data: t }) {
	let [n, r] = H(t.media_sources), [a, o] = H(""), s = G(null);
	U(() => () => s.current?.abort(), []);
	let c = async (e) => {
		if (s.current) return;
		let t = new AbortController();
		s.current = t, u(e, !0), o("");
		try {
			let e = await L(st, t.signal);
			t.signal.aborted || r(e.media_sources);
		} catch (e) {
			t.signal.aborted || o(I(e));
		} finally {
			s.current = null, u(e, !1);
		}
	};
	return n ? /* @__PURE__ */ K("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K(q, { html: i("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ K("dl", {
					class: "configfacts",
					children: n.map((t) => /* @__PURE__ */ K(N, { children: [/* @__PURE__ */ K("dt", { children: [/* @__PURE__ */ K("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: l(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ K("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ K("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				a ? /* @__PURE__ */ K("p", {
					class: "configbad",
					role: "alert",
					children: a
				}) : null
			]
		}), /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ K("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => c(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function mt({ value: t, label: n, onChange: r }) {
	let i = G(null), a = G(null), o = G(r);
	return o.current = r, W(() => {
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
	}, [n]), W(() => {
		a.current && (a.current.value = t);
	}, [t]), /* @__PURE__ */ K("div", {
		ref: i,
		class: "configsourcecontrol"
	});
}
function ht({ data: e, receipt: t }) {
	let n = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [r, a] = H(n?.length ? n.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [s, c] = H(n?.map((e) => e.location) ?? []), [l, d] = H(n?.map((e) => e.root) ?? []), [f, p] = H(String(e.port)), [m, h] = H(!1), [g, _] = H([]), [v, y] = H(""), [b, x] = H(""), [S, C] = H(null), [w, T] = H(null), E = G(!1), D = G(e.revision), O = G([]), k = G(null);
	W(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), U(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), lt);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		a((n) => n.map((n, r) => r === e ? t : n));
	}, ee = () => {
		T(r.length), a((e) => [...e, ""]);
	}, te = (e) => {
		c((t) => t.filter((t, n) => n !== e)), d((t) => t.filter((t, n) => n !== e)), a((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, j = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, ne = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			u(t, !0);
			try {
				let { path: t } = await R(ct, { initial: r[e] ?? "" });
				t && (A(e, t), j(e, ""));
			} catch (t) {
				j(e, I(t));
			} finally {
				u(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ K("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ K("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ K("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ K("use", { href: "#i-check" })
			}), /* @__PURE__ */ K("p", { children: /* @__PURE__ */ K("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ K("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ K("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !E.current) {
				E.current = !0, u(k.current, !0), x("");
				try {
					let n = await R(st, {
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
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(I(e)));
				} finally {
					E.current = !1, u(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ K("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ K(q, { html: i("configTitle", "这台电脑") }),
				/* @__PURE__ */ K("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ K("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ K("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: r.map((t, n) => /* @__PURE__ */ K("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ K("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ K("input", {
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
									/* @__PURE__ */ K("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => ne(n, e.currentTarget),
										children: /* @__PURE__ */ K("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ K("use", { href: "#i-folder-search" })
										})
									}),
									r.length > 1 ? /* @__PURE__ */ K("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => te(n),
										children: /* @__PURE__ */ K("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ K("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ K("div", {
										class: "configsource",
										children: [/* @__PURE__ */ K("div", {
											class: "configsourcelabel",
											children: ["媒体来源", /* @__PURE__ */ K(mt, {
												label: `媒体来源 ${n + 1}`,
												value: s[n] || "local",
												onChange: (e) => {
													let t = [...s];
													t[n] = e, c(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ K("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ K("input", {
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
									g[n] ? /* @__PURE__ */ K("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ K("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: ee,
							children: "添加文件夹"
						}),
						s.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ K("p", {
							class: "confighelp",
							children: ["先在 CloudDrive 登录网盘并完成挂载。", /* @__PURE__ */ K("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: ["挂载帮助", /* @__PURE__ */ K("svg", {
									"aria-hidden": "true",
									viewBox: "0 0 24 24",
									children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
								})]
							})]
						}) : null,
						s.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ K("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ K("a", {
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ K("svg", {
											"aria-hidden": "true",
											viewBox: "0 0 24 24",
											children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ K("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ K("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ K("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ K("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ K("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ K("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ K("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ K("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ K("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ K("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ K("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ K("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ K("span", { children: "保存后扫描并补全资料" })]
				}),
				b ? /* @__PURE__ */ K(q, { html: o(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ K("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ K("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ K("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function gt({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ K(q, {
		class: "configpage",
		html: o(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ K("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ K(it, {
				startup: t.startup,
				receipt: e
			}) : null,
			t.editable ? /* @__PURE__ */ K(ht, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ K(q, { html: o(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ K(pt, { data: t }),
			t.peach_proxy ? /* @__PURE__ */ K(nt, {
				initial: t.peach_proxy,
				receipt: e
			}) : null,
			t.access ? /* @__PURE__ */ K($e, {
				initial: t.access,
				receipt: e
			}) : null,
			t.updates ? /* @__PURE__ */ K(tt, {
				initial: t.updates,
				initialJob: t.update_job
			}) : null,
			/* @__PURE__ */ K(ft, { facts: t.facts }),
			t.uninstall ? /* @__PURE__ */ K(ot, { uninstall: t.uninstall }) : null
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var _t = Symbol.for("preact-signals");
function vt() {
	if (Y > 1) Y--;
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
		if (Ct = 0, Y--, t) throw e;
	}
}
function yt(e) {
	if (Y > 0) return e();
	Tt = ++wt, Y++;
	try {
		return e();
	} finally {
		vt();
	}
}
var bt, J = void 0;
function xt(e) {
	var t = J, n = bt;
	J = void 0, bt = void 0;
	try {
		return e();
	} finally {
		J = t, bt = n;
	}
}
var St = void 0, Y = 0, Ct = 0, wt = 0, Tt = 0, Et = void 0, Dt = 0;
function Ot(e) {
	if (J !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== J) return t = {
			i: 0,
			S: e,
			p: J.s,
			n: void 0,
			t: J,
			e: void 0,
			x: void 0,
			r: t
		}, J.s !== void 0 && (J.s.n = t), J.s = t, e.n = t, 32 & J.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = J.s, t.n = void 0, J.s.n = t, J.s = t), t;
	}
}
function X(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
X.prototype.brand = _t, X.prototype.h = function() {
	return !0;
}, X.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? xt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, X.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && xt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, X.prototype.subscribe = function(e) {
	var t = this;
	return Lt(function() {
		var n = t.value;
		xt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, X.prototype.valueOf = function() {
	return this.value;
}, X.prototype.toString = function() {
	return this.value + "";
}, X.prototype.toJSON = function() {
	return this.value;
}, X.prototype.peek = function() {
	var e = this;
	return xt(function() {
		return e.value;
	});
}, Object.defineProperty(X.prototype, "value", {
	get: function() {
		var e = Ot(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (Ct > 100) throw Error("Cycle detected");
			(function(e) {
				Y !== 0 && Ct === 0 && e.l !== Tt && (e.l = Tt, Et = {
					S: e,
					v: e.v,
					i: e.i,
					o: Et
				});
			})(this), this.v = e, this.i++, Dt++, Y++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				vt();
			}
		}
	}
});
function kt(e, t) {
	return new X(e, t);
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
function Z(e, t) {
	X.call(this, void 0, t), this.x = e, this.s = void 0, this.g = Dt - 1, this.f = 4;
}
Z.prototype = new X(), Z.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === Dt)) return !0;
	if (this.g = Dt, this.f |= 1, this.i > 0 && !At(this)) return this.f &= -2, !0;
	var e = J;
	try {
		jt(this), J = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return J = e, Mt(this), this.f &= -2, !0;
}, Z.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	X.prototype.S.call(this, e);
}, Z.prototype.U = function(e) {
	if (this.t !== void 0 && (X.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, Z.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(Z.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = Ot(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function Nt(e, t) {
	return new Z(e, t);
}
function Pt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		Y++;
		var n = J;
		J = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, Ft(e), t;
		} finally {
			J = n, vt();
		}
	}
}
function Ft(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Pt(e);
}
function It(e) {
	if (J !== this) throw Error("Out-of-order effect");
	Mt(this), J = e, this.f &= -2, 8 & this.f && Ft(this), vt();
}
function Q(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, bt && bt.push(this);
}
Q.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Q.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Pt(this), jt(this), Y++;
	var e = J;
	return J = this, It.bind(this, e);
}, Q.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = St, St = this);
}, Q.prototype.d = function() {
	this.f |= 8, 1 & this.f || Ft(this);
}, Q.prototype.dispose = function() {
	this.d();
};
function Lt(e, t) {
	var n = new Q(e, t);
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
var Rt, zt, Bt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Vt = [];
Lt(function() {
	Rt = this.N;
})();
function $(e, t) {
	y[e] = t.bind(null, y[e] || function() {});
}
function Ht(e) {
	if (zt) {
		var t = zt;
		zt = void 0, t();
	}
	zt = e && e.S();
}
function Ut(e) {
	var t = this, n = e.data, r = Gt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Ue(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = Nt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = Nt(function() {
			return !Array.isArray(i.value) && !x(i.value);
		}), o = Lt(function() {
			if (this.N = Jt, a.value) {
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
Ut.displayName = "ReactiveTextNode", Object.defineProperties(X.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Ut
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
}), $("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof X && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), $("__r", function(e, t) {
	if (e(t), t.type !== N) {
		Ht();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Lt(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				Bt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Ht(n);
	}
}), $("__e", function(e, t, n, r) {
	Ht(), e(t, n, r);
}), $("diffed", function(e, t) {
	Ht();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Wt(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Wt(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = kt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Lt(function() {
			this.N = Jt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
$("unmount", function(e, t) {
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
}), $("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), P.prototype.shouldComponentUpdate = function(e, t) {
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
function Gt(e, t) {
	return Ue(function() {
		return kt(e, t);
	}, []);
}
var Kt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function qt() {
	yt(function() {
		for (var e; e = Vt.shift();) Rt.call(e);
	});
}
function Jt() {
	Vt.push(this) === 1 && (y.requestAnimationFrame || Kt)(qt);
}
//#endregion
//#region src/state/quality-goals.ts
var Yt = "/api/quality-goals?limit=200", Xt = {
	data: null,
	error: ""
}, Zt = kt(Xt), Qt = 0, $t = Nt(() => Zt.value);
Nt(() => Zt.value.data?.total ?? null);
function en() {
	Qt += 1, Zt.value = Xt;
}
async function tn(e) {
	let t = Qt += 1;
	try {
		let n = await L(Yt, e);
		return t === Qt && (Zt.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === Qt && (Zt.value = {
			data: null,
			error: I(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var nn = (e, t) => tn(t), rn = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function an({ openItem: e, javTitleHtml: t, javDisplayName: n, srcBadge: i }) {
	let { data: a, error: s } = $t.value;
	if (s) return /* @__PURE__ */ K("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: o(s, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let c = a?.items ?? [];
	return c.length ? /* @__PURE__ */ K("div", {
		class: "qualitylist",
		children: c.map((r) => /* @__PURE__ */ K("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ K("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${n(r)}`,
				onClick: () => e(r.id),
				children: /* @__PURE__ */ K("img", {
					src: rn(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ K("div", { children: [
				/* @__PURE__ */ K("h3", { children: /* @__PURE__ */ K("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(r.id),
					dangerouslySetInnerHTML: { __html: t(r) }
				}) }),
				/* @__PURE__ */ K("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ K("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: i(r.location, r.cost) }
						}),
						/* @__PURE__ */ K("span", { children: p[r.location] ?? r.location }),
						/* @__PURE__ */ K("span", { children: h(r.duration) }),
						/* @__PURE__ */ K("span", { children: g(r.size ?? 0) })
					]
				}),
				r.reason ? /* @__PURE__ */ K("p", { children: r.reason }) : null
			] })]
		}, r.id))
	}) : /* @__PURE__ */ K("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function on(e) {
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
function sn(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	on({
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
var cn = (e, t) => L("/api/scraping", t);
function ln({ value: e, onChange: t }) {
	let n = G(null), r = G(t);
	return r.current = t, W(() => {
		let t = n.current;
		t.innerHTML = c([["peach", "Peach 代理"], ["direct", "直接连接"]], e, { label: "连接方式" });
		let i = f(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ K("div", {
		ref: n,
		class: "scraping-network"
	});
}
function un({ source: e, toast: t }) {
	let [n, r] = H(e), [a, s] = H(e.network), [c, l] = H(""), [d, f] = H(""), [p, h] = H("paste"), [g, _] = H(""), [v, y] = H(!1), [b, x] = H(""), [S, C] = H([]), w = G(null), T = G(null);
	W(() => {
		T.current?.querySelectorAll("footer button").forEach((e) => u(e, v));
	}, [v]);
	let E = G(new AbortController());
	U(() => () => E.current.abort(), []);
	async function D(n) {
		if (!v) {
			y(!0), x(""), C([]);
			try {
				if (n === "check") {
					let t = await R("/api/scraping/check", { source: e.source }, "POST", E.current.signal);
					E.current.signal.aborted || C(t.results);
				} else {
					let i = await R("/api/scraping/settings", {
						source: e.source,
						network: a,
						cookie: c,
						cookies_text: d,
						revoke: n === "revoke"
					}, "POST", E.current.signal);
					E.current.signal.aborted || (r(i.saved), l(""), f(""), _(""), w.current && (w.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				E.current.signal.aborted || x(I(e));
			} finally {
				E.current.signal.aborted || y(!1);
			}
		}
	}
	return /* @__PURE__ */ K("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ K("form", {
			ref: T,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), D("save");
			},
			children: [/* @__PURE__ */ K("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ K("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: [
							/* @__PURE__ */ K("img", {
								src: m(e.login),
								alt: "",
								width: "16",
								height: "16",
								loading: "lazy",
								onError: (e) => e.currentTarget.remove()
							}),
							/* @__PURE__ */ K("span", { children: e.login }),
							/* @__PURE__ */ K("svg", {
								"aria-hidden": "true",
								children: /* @__PURE__ */ K("use", { href: "#i-external-link" })
							})
						]
					}),
					/* @__PURE__ */ K("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ K(ln, {
							value: a,
							onChange: s
						})]
					}),
					a === "peach" && /* @__PURE__ */ K("a", {
						href: "/configuration#peachProxy",
						children: "配置 Peach 代理"
					}),
					e.accepts_cookie && /* @__PURE__ */ K(N, { children: [
						/* @__PURE__ */ K("p", { children: n.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ K("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ K("label", { children: [/* @__PURE__ */ K("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: p === t,
								onChange: () => {
									h(t), l(""), f(""), _("");
								}
							}), /* @__PURE__ */ K("span", { children: n })] }, t))
						}),
						p === "paste" ? /* @__PURE__ */ K("label", { children: ["Cookie", /* @__PURE__ */ K("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: c,
							disabled: v,
							onInput: (e) => l(e.currentTarget.value)
						})] }) : /* @__PURE__ */ K("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ K("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ K("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ K("span", {
										class: "scraping-file-name",
										children: g || "未选择文件"
									}),
									/* @__PURE__ */ K("input", {
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
					b && /* @__PURE__ */ K("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: o(b, { variant: "error" }) }
					}),
					S.map((t) => /* @__PURE__ */ K("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: o(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ K("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					e.accepts_cookie && n.cookie_saved && /* @__PURE__ */ K("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("revoke"),
						children: "撤销 Cookie"
					}),
					/* @__PURE__ */ K("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void D("check"),
						children: "检查连接"
					}),
					/* @__PURE__ */ K("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					})
				]
			})]
		})
	});
}
function dn({ data: e, error: t, toast: n }) {
	let [r, a] = H(""), [s, c] = H(!1), [l, d] = H(""), f = G(null);
	W(() => u(f.current, s), [s]);
	let p = G(new AbortController()), m = G(0);
	async function h(e = !1) {
		let t = ++m.current;
		await on({
			read: (e) => L("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				c(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && n(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	U(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!s) {
			m.current++, c(!0), d("");
			try {
				await R("/api/scraping/cover", { code: r }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (c(!1), d(I(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ K("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: o(t, { variant: "error" }) }
	}) : /* @__PURE__ */ K("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ K("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ K("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ K("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ K("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ K("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: r,
								disabled: s,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => a(e.currentTarget.value)
							}), /* @__PURE__ */ K("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						l && /* @__PURE__ */ K("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: o(l, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ K(un, {
				source: e,
				toast: n
			}, e.source))
		]
	});
}
//#endregion
//#region src/islands/library-processing.tsx
var fn = (e, t) => L("/api/library-processing", t);
function pn({ data: e, error: t, toast: n, onComplete: r, mode: c, monitor: l }) {
	let [d, f] = H(e || { status: "idle" }), [p, m] = H(t), [h, g] = H(!1), [_, v] = H(!1), y = G(new AbortController()), b = G(0), x = G(d.status), S = G(null), C = h || d.status === "running";
	W(() => u(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await on({
			read: (e) => L("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: c === "notice" || !!l,
			render: (e) => {
				f(e), m(""), e.status === "complete" && x.current === "running" && c !== "notice" && (v(!0), n("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && r?.(), x.current = e.status;
			},
			disconnected: () => m("连接中断，正在重新读取处理进度")
		});
	}
	U(() => ((d.status === "running" || c === "notice" || l) && w(), () => y.current.abort()), []);
	async function T() {
		if (!C) {
			g(!0), m(""), v(!1);
			try {
				let e = await R("/api/library-processing", {}, "POST", y.current.signal);
				if (y.current.signal.aborted) return;
				x.current = e.status, f(e), g(!1), await w();
			} catch (e) {
				y.current.signal.aborted || (m(I(e)), g(!1));
			}
		}
	}
	return c === "notice" ? !p && d.status !== "running" && d.status !== "failed" ? null : /* @__PURE__ */ K("div", {
		class: "library-processing-banner",
		role: "status",
		children: [/* @__PURE__ */ K("span", { children: p || (d.status === "failed" ? "扫描与资料采集未完成" : `${d.stage || "正在整理馆藏"}${d.total ? ` · ${d.checked || 0} / ${d.total}` : ""}`) }), /* @__PURE__ */ K("a", {
			class: "geist-button",
			href: "/data-cleanup#libraryProcessing",
			children: p || d.status === "failed" ? "查看并处理" : "查看进度"
		})]
	}) : /* @__PURE__ */ K(N, { children: [/* @__PURE__ */ K("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: i("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ K("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ K("div", {
				"aria-live": "polite",
				children: [
					d.status === "running" && /* @__PURE__ */ K(N, { children: [/* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: a(`${d.stage || "正在处理"}${d.total ? ` · ${d.checked || 0} / ${d.total}` : ""}`) } }), !!d.total && /* @__PURE__ */ K("div", { dangerouslySetInnerHTML: { __html: s(`已处理 ${d.checked || 0} / ${d.total} 个视频`, d.checked || 0, d.total) } })] }),
					(p || d.status === "failed") && /* @__PURE__ */ K("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: o(p || d.error || "处理未完成，请重试", { variant: "error" }) }
					}),
					d.status === "failed" && !!d.issues?.length && /* @__PURE__ */ K("ul", { children: d.issues.slice(0, 20).map((e) => /* @__PURE__ */ K("li", { children: [
						e.asset_id ? /* @__PURE__ */ K("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					_ && /* @__PURE__ */ K("div", {
						class: "library-processing-result",
						dangerouslySetInnerHTML: { __html: o(`已扫描 ${d.scanned || 0} 个文件，识别 ${d.identified || 0} 个番号，整理 ${d.candidates || 0} 组资料候选。`, {
							variant: "success",
							label: "处理完成"
						}) }
					})
				]
			})
		]
	}), /* @__PURE__ */ K("footer", {
		class: "geist-fieldset-footer",
		"data-geist-fieldset-footer": !0,
		children: [
			/* @__PURE__ */ K("a", {
				class: "geist-button",
				href: "/scraping",
				children: "采集来源"
			}),
			!!d.candidates && /* @__PURE__ */ K("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			/* @__PURE__ */ K("button", {
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
var mn = { "quality-goals": {
	refresh: tn,
	reset: en
} }, hn = () => Object.keys(mn);
async function gn(e) {
	let t = mn[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/review-bulk.ts
var _n = () => ({
	active: !1,
	busy: !1,
	selected: /* @__PURE__ */ new Set(),
	choices: /* @__PURE__ */ new Map(),
	assets: /* @__PURE__ */ new Map(),
	errors: /* @__PURE__ */ new Map()
});
async function vn(e, t, n, r) {
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
				message: I(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function yn(e, n) {
	let r = e.querySelector(".reviewlist");
	if (!r || !n.rows.length || n.locked) return;
	let i = n.state, a = [...r.querySelectorAll("[data-review-key]")], o = document.createElement("div");
	o.className = "reviewbulkbar";
	let s = document.createElement("button");
	s.className = "geist-button", s.type = "button", o.append(s), r.before(o);
	let c = n.metadata ? [{
		title: "单一候选",
		cards: a.filter((e) => (n.rows.find((t) => t.item_key === e.dataset.reviewKey)?.candidates?.length || 0) === 1)
	}, {
		title: "需选择来源",
		cards: a.filter((e) => (n.rows.find((t) => t.item_key === e.dataset.reviewKey)?.candidates?.length || 0) !== 1)
	}] : [{
		title: "待复核",
		cards: a
	}];
	r.classList.add("reviewgroups");
	let l = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, d = [];
	for (let a of c.filter((e) => e.cards.length)) {
		let o = document.createElement("section");
		o.className = "reviewgroup";
		let s = document.createElement("div");
		s.className = "reviewbulkbar";
		let c = document.createElement("h3");
		c.textContent = `${a.title} · ${a.cards.length}`;
		let p = document.createElement("button");
		p.className = "geist-button", p.type = "button";
		let m = document.createElement("button");
		m.className = "geist-button", m.type = "button";
		let h = document.createElement("p");
		h.className = "reviewstate", h.setAttribute("role", "status");
		let g = document.createElement("div");
		g.className = "reviewlist", s.append(c, p, m), o.append(s, h, g), r.append(o);
		for (let e of a.cards) {
			g.append(e);
			let n = e.dataset.reviewKey, r = l(e);
			i.errors.has(n) && (e.querySelector(".reviewstate").textContent = i.errors.get(n));
			let a = document.createElement("label");
			a.className = "reviewpickitem", a.innerHTML = t("aria-label=\"选择此复核项\"") + "<span>选择此项</span>";
			let o = a.querySelector("input");
			if (e.prepend(a), i.assets.has(n)) {
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
				t.checked && i.choices.set(n, t.value);
			});
			o.onchange = () => {
				o.checked ? i.selected.add(n) : i.selected.delete(n), f();
			}, d.push(() => {
				a.hidden = !i.active, o.checked = i.selected.has(n), o.disabled = !r;
			});
		}
		let _ = () => a.cards.filter((e) => i.selected.has(e.dataset.reviewKey) && l(e));
		d.push(() => {
			p.hidden = m.hidden = !i.active, p.textContent = _().length && _().length === a.cards.filter(l).length ? "清空本组" : "全选本组", m.textContent = `采用所选${_().length ? `（${_().length}）` : ""}`, m.disabled = !_().length, p.disabled = !a.cards.some(l);
		}), p.onclick = () => {
			if (i.busy) return;
			let e = a.cards.filter(l), t = _().length === e.length;
			e.forEach((e) => t ? i.selected.delete(e.dataset.reviewKey) : i.selected.add(e.dataset.reviewKey)), f();
		}, m.onclick = async () => {
			if (i.busy || !_().length) return;
			let t = _().map((e) => ({
				key: e.dataset.reviewKey,
				payload: n.payload(e)
			}));
			if (n.metadata && t.some((e) => !e.payload.candidate_key)) {
				h.textContent = "请先为所选的多来源候选选择来源。", _().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
				return;
			}
			i.busy = !0, h.textContent = `正在采用 0 / ${t.length}`, f(), u(m, !0);
			let r = [...e.querySelectorAll("button,input")], a = r.map((e) => e.getAttribute("aria-disabled"));
			r.forEach((e) => {
				e.setAttribute("aria-disabled", "true");
			});
			let o = (e) => {
				e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
			};
			e.addEventListener("click", o, !0), e.addEventListener("keydown", o, !0);
			let s = 0, c = await vn(t, async (e) => {
				try {
					return await n.submit(e);
				} finally {
					s++, n.active() && (h.textContent = `正在采用 ${s} / ${t.length}`);
				}
			}, (e) => {
				i.selected.delete(e), i.errors.delete(e), n.applied(e);
			}, n.active);
			if (i.busy = !1, e.removeEventListener("click", o, !0), e.removeEventListener("keydown", o, !0), r.forEach((e, t) => {
				let n = a[t];
				n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
			}), u(m, !1), !n.active()) return;
			n.notify(`已采用 ${c.completed} 项${c.failures.length ? `，${c.failures.length} 项未完成` : ""}`), c.failures.forEach((e) => i.errors.set(e.key, e.message));
			let l = e.parentElement;
			n.refresh(), l?.querySelector(".reviewbulkbar button")?.focus({ preventScroll: !0 });
		};
	}
	function f() {
		s.textContent = i.active ? "退出多选" : "多选", s.setAttribute("aria-pressed", String(i.active)), d.forEach((e) => e());
	}
	s.onclick = () => {
		i.busy || (i.active = !i.active, i.active || i.selected.clear(), f());
	}, f();
}
//#endregion
//#region src/native-image.ts
function bn(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function xn(e, t, n, r, i = 1) {
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
function Sn(e, t) {
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
var Cn = [
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
function wn() {
	let e = (e) => [
		,
		,
		,
	].fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function Tn(e, t) {
	let n = new URLSearchParams();
	for (let t of Cn) e[t] && n.set(t, e[t]);
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
function En({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: i = !1, online: a = !1 } = {}) {
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
function Dn(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function On(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function kn(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function An(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function jn(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function Mn() {
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
function Nn(e, t = !1, n = !1) {
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
var Pn = "peach-taste-guide-dismissed";
function Fn(e, t) {
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(Pn, "1"), n.remove();
	});
}
//#endregion
//#region src/jav-artwork.ts
function In(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function Ln(e) {
	return {
		javLayout: In(e.javLayout),
		javImage: Rn(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Rn(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function zn(e, t) {
	return e.is_jav && e.code && e.has_cover && (Rn(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function Bn(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Rn(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var Vn = {
	"library-processing": {
		load: fn,
		component: pn
	},
	scraping: {
		load: cn,
		component: dn
	},
	"quality-goals": {
		load: nn,
		component: an
	},
	configuration: {
		load: ut,
		component: gt
	}
}, Hn = () => Object.keys(Vn), Un = /* @__PURE__ */ new Map();
async function Wn(e, t, n, r = {}) {
	let i = Vn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Gn(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	Un.set(t, a);
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
			error: I(e)
		};
	}
	if (Un.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		Un.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	De(oe(i.component, s), t);
}
function Gn(e) {
	let t = Un.get(e);
	t && (t.controller.abort(), Un.delete(e), t.painted && De(null, e));
}
//#endregion
export { Pn as TASTE_GUIDE_KEY, En as catalogEmptyHtml, Tn as catalogSuggestions, Mn as cleanupSkeletonHtml, An as cloudLocations, jn as cloudPreferenceLocations, _n as createReviewSelection, wn as emptyCatalogLayout, Sn as entitySkeletonHtml, sn as followJobProgress, Hn as islandNames, zn as javImageKind, bn as matchesFaceSource, Wn as mountIsland, xn as nativeImageFit, Rn as normalizeJavImage, In as normalizeJavLayout, Ln as normalizeJavPreferences, Oe as preferredDirection, gn as refreshStore, Dn as sidebarHasCatalogContent, kn as sidebarTagCounts, hn as storeNames, Bn as syncJavImages, On as syncSidebarSurface, Nn as tasteHistoryGuideHtml, Gn as unmountIsland, on as watchJob, yn as wireReviewSelection, Fn as wireTasteHistoryGuide };
