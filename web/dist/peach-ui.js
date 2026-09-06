import { MEDIA_SOURCE_ICONS as e, emptyStateHtml as t, fieldsetTitle as n, loadingDotsHtml as r, noteHtml as i, progressHtml as a, selectFieldHtml as o, selectOptionIconHtml as s, setActionBusy as c, wireSelectField as l } from "/js/ui-components.js";
import { LOC as u, fmtDur as d, fmtSize as f } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var p, m, h, g, _, v, y, b, x, S, C, w, T, E, D, O = {}, k = [], ee = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, te = Array.isArray;
function A(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function j(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function ne(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? p.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return re(e, o, r, i, null);
}
function re(e, t, n, r, i) {
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
		__v: i ?? ++h,
		__i: -1,
		__u: 0
	};
	return i == null && m.vnode != null && m.vnode(a), a;
}
function M(e) {
	return e.children;
}
function N(e, t) {
	this.props = e, this.context = t;
}
function P(e, t) {
	if (t == null) return e.__ ? P(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? P(e) : null;
}
function ie(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = A({}, t);
		a.__v = t.__v + 1, m.vnode && m.vnode(a), he(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? P(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, _e(r, a, i), t.__e = t.__ = null, a.__e != n && ae(a);
	}
}
function ae(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), ae(e);
}
function oe(e) {
	(!e.__d && (e.__d = !0) && _.push(e) && !se.__r++ || v != m.debounceRendering) && ((v = m.debounceRendering) || y)(se);
}
function se() {
	try {
		for (var e, t = 1; _.length;) _.length > t && _.sort(b), e = _.shift(), t = _.length, ie(e);
	} finally {
		_.length = se.__r = 0;
	}
}
function ce(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || k, v = t.length;
	for (c = le(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || O, p.__i = d, g = he(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && be(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = ue(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function le(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = re(null, o, null, null, null) : te(o) ? o = e.__k[a] = re(M, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = re(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = de(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = P(s)), xe(s, s));
	return r;
}
function ue(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = ue(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = P(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function de(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function fe(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || ee.test(t) ? n : n + "px";
}
function pe(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || fe(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || fe(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(w, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[C] = r[C] : (n[C] = T, e.addEventListener(t, a ? D : E, a)) : e.removeEventListener(t, a ? D : E, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function me(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[S] == null) t[S] = T++;
			else if (t[S] < n[C]) return;
			return n(m.event ? m.event(t) : t);
		}
	};
}
function he(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, h, g, _, v, y, b, x, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = m.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (y = t.props, b = D.prototype && D.prototype.render, x = (u = D.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? v = (f = t.__c = n.__c).__ = f.__E : (b ? t.__c = f = new D(y, S) : (t.__c = f = new N(y, S), f.constructor = D, f.render = Se), x && x.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), b && f.__s == null && (f.__s = f.state), b && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = A({}, f.__s)), A(f.__s, D.getDerivedStateFromProps(y, f.__s))), h = f.props, g = f.state, f.__v = t, p) b && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), b && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (b && D.getDerivedStateFromProps == null && y !== h && f.componentWillReceiveProps != null && f.componentWillReceiveProps(y, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(y, f.__s, S)) {
					t.__v != n.__v && (f.props = y, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), k.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = P(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(y, f.__s, S), b && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(h, g, _);
				});
			}
			if (f.context = S, f.props = y, f.__P = e, f.__e = !1, C = m.__r, w = 0, b) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), k.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = A(A({}, r), f.getChildContext())), b && !p && f.getSnapshotBeforeUpdate != null && (_ = f.getSnapshotBeforeUpdate(h, g)), T = u != null && u.type === M && u.key == null ? ve(u.props.children) : u, s = ce(e, te(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), v && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) j(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || ge(t), m.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = ye(n.__e, t, n, r, i, a, o, c, l);
	return (u = m.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function ge(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(ge));
}
function _e(e, t, n) {
	for (var r = 0; r < n.length; r++) be(n[r], n[++r], n[++r]);
	m.__c && m.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			m.__e(e, t.__v);
		}
	});
}
function ve(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : te(e) ? e.map(ve) : e.constructor === void 0 ? A({}, e) : null;
}
function ye(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, h, g, _, v = n.props || O, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((h = a[l]) && "setAttribute" in h == !!b && (b ? h.localName == b : h.nodeType == 3)) {
			e = h, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), s &&= (m.__m && m.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || s && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && p.call(e.childNodes), !s && a != null) for (v = {}, l = 0; l < e.attributes.length; l++) v[(h = e.attributes[l]).name] = h.value;
		for (l in v) h = v[l], l == "dangerouslySetInnerHTML" ? d = h : l == "children" || l in y || l == "value" && "defaultValue" in y || l == "checked" && "defaultChecked" in y || pe(e, l, null, h, i);
		for (l in y) h = y[l], l == "children" ? f = h : l == "dangerouslySetInnerHTML" ? u = h : l == "value" ? g = h : l == "checked" ? _ = h : s && typeof h != "function" || v[l] === h || pe(e, l, h, v[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), ce(t.type == "template" ? e.content : e, te(f) ? f : [f], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && P(n, 0), s, c), a != null) for (l = a.length; l--;) j(a[l]);
		s && b != "textarea" || (l = "value", b == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[l] || b == "progress" && !g || b == "option" && g != v[l]) && pe(e, l, g, v[l], i), l = "checked", _ != null && _ != e[l] && pe(e, l, _, v[l], i));
	}
	return e;
}
function be(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		m.__e(e, n);
	}
}
function xe(e, t, n) {
	var r, i;
	if (m.unmount && m.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || be(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			m.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && xe(r[i], t, n || typeof e.type != "function");
	n || j(e.__e), e.__c = e.__ = e.__e = void 0;
}
function Se(e, t, n) {
	return this.constructor(e, n);
}
function Ce(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), m.__ && m.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], he(t, e = (!r && n || t).__k = ne(M, null, [e]), i || O, O, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? p.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), _e(a, e, o), e.props.children = null;
}
p = k.slice, m = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, h = 0, g = function(e) {
	return e != null && e.constructor === void 0;
}, N.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = A({}, this.state);
	typeof e == "function" && (e = e(A({}, n), this.props)), e && A(n, e), e != null && this.__v && (t && this._sb.push(t), oe(this));
}, N.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), oe(this));
}, N.prototype.render = M, _ = [], y = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, b = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, se.__r = 0, x = Math.random().toString(8), S = "__d" + x, C = "__a" + x, w = /(PointerCapture)$|Capture$/i, T = 0, E = me(!1), D = me(!0);
//#endregion
//#region src/api.ts
var we = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Te = (e) => {
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
	if (!n.ok) throw new we(Te(r) || `请求失败（${n.status}）`, n.status);
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
	if (!i.ok) throw new we(Te(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var R, z, Ee, De, Oe = 0, ke = [], B = m, Ae = B.__b, je = B.__r, Me = B.diffed, Ne = B.__c, Pe = B.unmount, Fe = B.__;
function Ie(e, t) {
	B.__h && B.__h(z, e, Oe || t), Oe = 0;
	var n = z.__H || (z.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function V(e) {
	return Oe = 1, Le(Ke, e);
}
function Le(e, t, n) {
	var r = Ie(R++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Ke(void 0, t), function(e) {
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
function Re(e, t) {
	var n = Ie(R++, 3);
	!B.__s && Ge(n.__H, t) && (n.__ = e, n.u = t, z.__H.__h.push(n));
}
function H(e, t) {
	var n = Ie(R++, 4);
	!B.__s && Ge(n.__H, t) && (n.__ = e, n.u = t, z.__h.push(n));
}
function U(e) {
	return Oe = 5, ze(function() {
		return { current: e };
	}, []);
}
function ze(e, t) {
	var n = Ie(R++, 7);
	return Ge(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Be() {
	for (var e; e = ke.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Ue), t.__h.some(We), t.__h = [];
		} catch (n) {
			t.__h = [], B.__e(n, e.__v);
		}
	}
}
B.__b = function(e) {
	z = null, Ae && Ae(e);
}, B.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Fe && Fe(e, t);
}, B.__r = function(e) {
	je && je(e), R = 0;
	var t = (z = e.__c).__H;
	t && (Ee === z ? (t.__h = [], z.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Ue), t.__h.some(We), t.__h = [], R = 0)), Ee = z;
}, B.diffed = function(e) {
	Me && Me(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (ke.push(t) !== 1 && De === B.requestAnimationFrame || ((De = B.requestAnimationFrame) || He)(Be)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ee = z = null;
}, B.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Ue), e.__h = e.__h.filter(function(e) {
				return !e.__ || We(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], B.__e(n, e.__v);
		}
	}), Ne && Ne(e, t);
}, B.unmount = function(e) {
	Pe && Pe(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Ue(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && B.__e(t, n.__v));
};
var Ve = typeof requestAnimationFrame == "function";
function He(e) {
	var t, n = function() {
		clearTimeout(r), Ve && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Ve && (t = requestAnimationFrame(n));
}
function Ue(e) {
	var t = z, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), z = t;
}
function We(e) {
	var t = z;
	e.__c = e.__(), z = t;
}
function Ge(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function Ke(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var qe = 0;
Array.isArray;
function W(e, t, n, r, i, a) {
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
		__v: --qe,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return m.vnode && m.vnode(l), l;
}
//#endregion
//#region src/islands/access-settings.tsx
function Je({ id: e, label: t, value: n, onInput: r, error: i, help: a, current: o = !1 }) {
	return /* @__PURE__ */ W("div", {
		class: "configfield",
		children: [
			/* @__PURE__ */ W("label", {
				for: e,
				children: t
			}),
			/* @__PURE__ */ W("input", {
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
			i || a ? /* @__PURE__ */ W("p", {
				id: `${e}-hint`,
				class: i ? "configbad" : "confighelp",
				role: i ? "alert" : void 0,
				children: i || a
			}) : null
		]
	});
}
function Ye({ initial: e, receipt: t }) {
	let [r, i] = V(e), [a, o] = V(""), [s, l] = V(""), [u, d] = V(""), [f, p] = V(!1), [m, h] = V(""), [g, _] = V({}), v = U(null), y = U(!1), b = U(null);
	return /* @__PURE__ */ W("form", {
		class: "configfieldset",
		onSubmit: async (e) => {
			if (e.preventDefault(), y.current) return;
			h("");
			let n = {};
			if (r.mode === "password" && !a && (n.current_password = "请输入当前访问密码"), f || ((s.length < 8 || s.length > 256) && (n.password = "访问密码需为 8–256 个字符"), s !== u && (n.confirmation = "两次输入的密码不一致")), _(n), Object.keys(n).length) {
				requestAnimationFrame(() => v.current?.querySelector("[aria-invalid=\"true\"]")?.focus());
				return;
			}
			y.current = !0, c(b.current, !0);
			try {
				let e = await L("/api/configuration/access", {
					revision: r.revision,
					action: f ? "disable" : "set",
					confirm_disable: f,
					current_password: a,
					password: f ? "" : s,
					confirmation: f ? "" : u
				});
				i(e), o(""), l(""), d(""), p(!1), _({}), t(e.mode === "open" ? "已关闭访问密码" : "已保存访问密码");
			} catch (e) {
				let t = e instanceof we ? e.body : null, n = t?.errors || t?.detail?.errors;
				n ? _(n) : h(F(e));
			} finally {
				y.current = !1, c(b.current, !1);
			}
		},
		"aria-labelledby": "accessTitle",
		noValidate: !0,
		ref: v,
		children: [/* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ W("div", {
					class: "configfieldset-heading",
					children: [/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n("accessTitle", "访问密码") } }), /* @__PURE__ */ W("p", {
						class: "confighelp",
						children: r.mode === "open" ? "未设置密码，能连接到 Peach 的设备可直接访问。" : r.mode === "legacy" ? "当前使用系统生成的访问口令。你可以设置自己的密码，或关闭登录要求。" : r.mode === "locked" ? "访问设置无法读取，请在本机检查配置文件。" : "已设置密码。新设备需要登录，保持登录时间在登录页选择。"
					})]
				}),
				r.mode === "password" ? /* @__PURE__ */ W(Je, {
					id: "access-current",
					label: "当前访问密码",
					value: a,
					onInput: o,
					error: g.current_password,
					current: !0
				}) : null,
				!f && r.mode !== "locked" ? /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W(Je, {
					id: "access-password",
					label: r.mode === "password" ? "新访问密码" : "设置访问密码",
					value: s,
					onInput: l,
					error: g.password,
					help: "至少 8 个字符。保存后其他设备需要重新登录。"
				}), /* @__PURE__ */ W(Je, {
					id: "access-confirm",
					label: "确认访问密码",
					value: u,
					onInput: d,
					error: g.confirmation
				})] }) : null,
				r.mode === "password" || r.mode === "legacy" ? /* @__PURE__ */ W("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ W("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ W("input", {
							type: "checkbox",
							checked: f,
							onChange: (e) => p(e.currentTarget.checked)
						}), /* @__PURE__ */ W("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ W("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ W("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ W("span", { children: "关闭访问密码，允许能连接到 Peach 的设备直接访问" })]
				}) : null,
				m ? /* @__PURE__ */ W("p", {
					class: "configbad",
					role: "alert",
					children: m
				}) : null
			]
		}), r.mode === "locked" ? null : /* @__PURE__ */ W("div", {
			class: "geist-fieldset-footer",
			children: [/* @__PURE__ */ W("p", { children: "保存后立即生效。" }), /* @__PURE__ */ W("button", {
				class: "geist-button primary",
				type: "submit",
				ref: b,
				children: "保存配置"
			})]
		})]
	});
}
//#endregion
//#region src/jobs.ts
async function Xe(e) {
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
function Ze(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	Xe({
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
//#region src/islands/library-processing.tsx
var Qe = (e, t) => I("/api/library-processing", t);
function $e({ data: e, error: t, toast: o, onComplete: s, mode: l, monitor: u }) {
	let [d, f] = V(e || { status: "idle" }), [p, m] = V(t), [h, g] = V(!1), [_, v] = V(!1), y = U(new AbortController()), b = U(0), x = U(d.status), S = U(null), C = h || d.status === "running";
	H(() => c(S.current, C), [C]);
	async function w() {
		let e = ++b.current;
		await Xe({
			read: (e) => I("/api/library-processing", e),
			active: () => !y.current.signal.aborted && b.current === e,
			keepWatching: l === "notice" || !!u,
			render: (e) => {
				f(e), m(""), e.status === "complete" && x.current === "running" && l !== "notice" && (v(!0), o("已完成扫描与资料采集")), x.current === "running" && (e.status === "complete" || e.status === "failed") && s?.(), x.current = e.status;
			},
			disconnected: () => m("连接中断，正在重新读取处理进度")
		});
	}
	Re(() => ((d.status === "running" || l === "notice" || u) && w(), () => y.current.abort()), []);
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
	return l === "notice" ? !p && d.status !== "running" && d.status !== "failed" ? null : /* @__PURE__ */ W("div", {
		class: "library-processing-banner",
		role: "status",
		children: [/* @__PURE__ */ W("span", { children: p || (d.status === "failed" ? "扫描与资料采集未完成" : `${d.stage || "正在整理馆藏"}${d.total ? ` · ${d.checked || 0} / ${d.total}` : ""}`) }), /* @__PURE__ */ W("a", {
			class: "geist-button",
			href: "/configuration#libraryProcessing",
			children: p || d.status === "failed" ? "查看并处理" : "查看进度"
		})]
	}) : /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W("div", {
		class: "geist-fieldset-content library-processing",
		children: [
			/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n("cleanupScrapingTitle", "扫描与采集") } }),
			/* @__PURE__ */ W("p", { children: "扫描媒体文件夹，导入已有资料，采集缺失信息。" }),
			/* @__PURE__ */ W("div", {
				"aria-live": "polite",
				children: [
					d.status === "running" && /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: r(`${d.stage || "正在处理"}${d.total ? ` · ${d.checked || 0} / ${d.total}` : ""}`) } }), !!d.total && /* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: a(`已处理 ${d.checked || 0} / ${d.total} 个视频`, d.checked || 0, d.total) } })] }),
					(p || d.status === "failed") && /* @__PURE__ */ W("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: i(p || d.error || "处理未完成，请重试", { variant: "error" }) }
					}),
					d.status === "failed" && !!d.issues?.length && /* @__PURE__ */ W("ul", { children: d.issues.slice(0, 20).map((e) => /* @__PURE__ */ W("li", { children: [
						e.asset_id ? /* @__PURE__ */ W("a", {
							href: `/item/${e.asset_id}`,
							children: "查看视频"
						}) : null,
						e.asset_id ? "：" : "",
						e.message
					] })) }),
					_ && /* @__PURE__ */ W("p", { children: [
						"已扫描 ",
						d.scanned || 0,
						" 个文件，识别 ",
						d.identified || 0,
						" 个番号，整理 ",
						d.candidates || 0,
						" 组资料候选。"
					] })
				]
			})
		]
	}), /* @__PURE__ */ W("footer", {
		class: "geist-fieldset-footer",
		"data-geist-fieldset-footer": !0,
		children: [
			/* @__PURE__ */ W("a", {
				class: "geist-button",
				href: "/scraping",
				children: "采集来源"
			}),
			!!d.candidates && /* @__PURE__ */ W("a", {
				class: "geist-button",
				href: "/review",
				children: "复核资料"
			}),
			/* @__PURE__ */ W("button", {
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
//#region src/islands/configuration.tsx
var et = "/api/configuration", tt = "/api/pick-folder", nt = 8e3, rt = (e, t) => Promise.all([I(et, t), I("/api/library-processing", t).catch((e) => ({
	status: "failed",
	error: F(e)
}))]).then(([e, t]) => ({
	...e,
	processing: t
})), G = ({ html: e, class: t }) => /* @__PURE__ */ W("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), it = (e) => !(e instanceof we) || e.status !== 400 ? null : e.body?.errors ?? null;
function at({ facts: e }) {
	return /* @__PURE__ */ W("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ W(G, { html: n("configFactsTitle", "运行信息") }), /* @__PURE__ */ W("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W("dt", { children: e.term }), /* @__PURE__ */ W("dd", { children: [e.value, e.download_url ? /* @__PURE__ */ W("span", {
					class: "confighelp",
					children: [" ", /* @__PURE__ */ W("a", {
						href: e.download_url,
						target: "_blank",
						rel: "noreferrer",
						children: [e.download_label, /* @__PURE__ */ W("svg", {
							"aria-hidden": "true",
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ W("use", { href: "#i-external-link" })
						})]
					})]
				}) : null] })] }))
			})]
		})
	});
}
function ot({ data: t }) {
	let [r, i] = V(t.media_sources), [a, o] = V(""), l = U(null);
	Re(() => () => l.current?.abort(), []);
	let u = async (e) => {
		if (l.current) return;
		let t = new AbortController();
		l.current = t, c(e, !0), o("");
		try {
			let e = await I(et, t.signal);
			t.signal.aborted || i(e.media_sources);
		} catch (e) {
			t.signal.aborted || o(F(e));
		} finally {
			l.current = null, c(e, !1);
		}
	};
	return r ? /* @__PURE__ */ W("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: [/* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ W(G, { html: n("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ W("dl", {
					class: "configfacts",
					children: r.map((t) => /* @__PURE__ */ W(M, { children: [/* @__PURE__ */ W("dt", { children: [/* @__PURE__ */ W("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: s(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ W("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ W("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				a ? /* @__PURE__ */ W("p", {
					class: "configbad",
					role: "alert",
					children: a
				}) : null
			]
		}), /* @__PURE__ */ W("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: /* @__PURE__ */ W("button", {
				type: "button",
				class: "geist-button",
				onClick: (e) => u(e.currentTarget),
				children: "刷新挂载状态"
			})
		})]
	}) : null;
}
function st({ value: t, label: n, onChange: r }) {
	let i = U(null), a = U(null), s = U(r);
	return s.current = r, H(() => {
		let r = i.current;
		r.innerHTML = o([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([t, n]) => [
			t,
			n,
			e[t]
		]), t, { label: n });
		let c = l(r.firstElementChild);
		a.current = c;
		let u = () => s.current(c.value);
		return c.addEventListener("change", u), () => {
			a.current = null, c.disabled = !0, c.removeEventListener("change", u), r.replaceChildren();
		};
	}, [n]), H(() => {
		a.current && (a.current.value = t);
	}, [t]), /* @__PURE__ */ W("div", {
		ref: i,
		class: "configsourcecontrol"
	});
}
function ct({ data: e, receipt: t }) {
	let r = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [a, o] = V(r?.length ? r.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [s, l] = V(r?.map((e) => e.location) ?? []), [u, d] = V(r?.map((e) => e.root) ?? []), [f, p] = V(String(e.port)), [m, h] = V(!1), [g, _] = V([]), [v, y] = V(""), [b, x] = V(""), [S, C] = V(null), [w, T] = V(null), E = U(!1), D = U(e.revision), O = U([]), k = U(null);
	H(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), Re(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), nt);
		return () => clearTimeout(e);
	}, [S]);
	let ee = (e, t) => {
		o((n) => n.map((n, r) => r === e ? t : n));
	}, te = () => {
		T(a.length), o((e) => [...e, ""]);
	}, A = (e) => {
		l((t) => t.filter((t, n) => n !== e)), d((t) => t.filter((t, n) => n !== e)), o((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, j = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, ne = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			c(t, !0);
			try {
				let { path: t } = await L(tt, { initial: a[e] ?? "" });
				t && (ee(e, t), j(e, ""));
			} catch (t) {
				j(e, F(t));
			} finally {
				c(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ W("div", {
		class: "configsaved",
		role: "status",
		children: /* @__PURE__ */ W("div", {
			class: "geist-note geist-note-success",
			role: "note",
			children: [/* @__PURE__ */ W("svg", {
				"aria-hidden": "true",
				viewBox: "0 0 24 24",
				children: /* @__PURE__ */ W("use", { href: "#i-check" })
			}), /* @__PURE__ */ W("p", { children: /* @__PURE__ */ W("span", { children: [
				"配置已保存，Peach 正在重新启动。稍后自动跳转，或点击",
				/* @__PURE__ */ W("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			] }) })]
		})
	}) : /* @__PURE__ */ W("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !E.current) {
				E.current = !0, c(k.current, !0), x("");
				try {
					let n = await L(et, {
						revision: D.current,
						media_dirs: a,
						...e.media_sources ? { media_sources: a.map((e, t) => ({
							path: e,
							location: s[t] || "local",
							root: u[t] || ""
						})) } : {},
						port: f,
						scan_now: m
					});
					D.current = n.revision, _([]), y(""), t("已保存配置"), C(n);
				} catch (e) {
					let t = it(e);
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(F(e)));
				} finally {
					E.current = !1, c(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ W("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ W(G, { html: n("configTitle", "这台电脑") }),
				/* @__PURE__ */ W("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ W("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ W("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: a.map((t, n) => /* @__PURE__ */ W("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ W("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ W("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": g[n] ? "true" : void 0,
										onInput: (e) => ee(n, e.currentTarget.value),
										ref: (e) => {
											O.current[n] = e;
										}
									}),
									/* @__PURE__ */ W("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => ne(n, e.currentTarget),
										children: /* @__PURE__ */ W("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ W("use", { href: "#i-folder-search" })
										})
									}),
									a.length > 1 ? /* @__PURE__ */ W("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => A(n),
										children: /* @__PURE__ */ W("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ W("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ W("div", {
										class: "configsource",
										children: [/* @__PURE__ */ W("div", {
											class: "configsourcelabel",
											children: ["媒体来源", /* @__PURE__ */ W(st, {
												label: `媒体来源 ${n + 1}`,
												value: s[n] || "local",
												onChange: (e) => {
													let t = [...s];
													t[n] = e, l(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ W("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ W("input", {
											class: "geist-input",
											"aria-label": `Windows 中的对应路径 ${n + 1}`,
											value: u[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...u];
												t[n] = e.currentTarget.value, d(t);
											}
										})] }) : null]
									}),
									g[n] ? /* @__PURE__ */ W("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ W("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: te,
							children: "添加文件夹"
						}),
						s.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ W("p", {
							class: "confighelp",
							children: ["先在 CloudDrive 登录网盘并完成挂载。", /* @__PURE__ */ W("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: ["挂载帮助", /* @__PURE__ */ W("svg", {
									"aria-hidden": "true",
									viewBox: "0 0 24 24",
									children: /* @__PURE__ */ W("use", { href: "#i-external-link" })
								})]
							})]
						}) : null,
						s.some((e) => e === "115" || e === "pikpak") ? e.mount_dependencies?.filter((e) => !e.available).map((e) => /* @__PURE__ */ W("p", {
							class: "confighelp",
							children: [
								"未检测到 ",
								e.name,
								"。",
								/* @__PURE__ */ W("a", {
									href: e.download_url,
									target: "_blank",
									rel: "noreferrer",
									children: [
										"下载 ",
										e.name,
										/* @__PURE__ */ W("svg", {
											"aria-hidden": "true",
											viewBox: "0 0 24 24",
											children: /* @__PURE__ */ W("use", { href: "#i-external-link" })
										})
									]
								})
							]
						})) : null,
						e.windows === !1 ? /* @__PURE__ */ W("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				e.port_editable === !1 ? null : /* @__PURE__ */ W("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ W("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ W("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ W("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ W("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ W("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ W("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ W("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ W("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ W("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ W("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ W("span", { children: "保存后扫描并补全资料" })]
				}),
				b ? /* @__PURE__ */ W(G, { html: i(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ W("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ W("p", { children: e.port_editable === !1 ? "保存后 Peach 会重新载入配置。" : "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ W("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function lt({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ W(G, {
		class: "configpage",
		html: i(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ W("div", {
		class: "configpage",
		children: [
			t.editable ? /* @__PURE__ */ W(ct, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ W(G, { html: i(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			t.access ? /* @__PURE__ */ W(Ye, {
				initial: t.access,
				receipt: e
			}) : null,
			/* @__PURE__ */ W("section", {
				id: "libraryProcessing",
				class: "configfieldset",
				"data-geist-fieldset": !0,
				"aria-labelledby": "cleanupScrapingTitle",
				children: /* @__PURE__ */ W($e, {
					data: t.processing || { status: "idle" },
					error: "",
					toast: e,
					monitor: !0
				})
			}),
			/* @__PURE__ */ W(at, { facts: t.facts }),
			/* @__PURE__ */ W(ot, { data: t })
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var ut = Symbol.for("preact-signals");
function dt() {
	if (Y > 1) Y--;
	else {
		var e, t = !1;
		for ((function() {
			var e = _t;
			for (_t = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); J !== void 0;) {
			var n = J;
			for (J = void 0, mt++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && xt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (mt = 0, Y--, t) throw e;
	}
}
function ft(e) {
	if (Y > 0) return e();
	gt = ++ht, Y++;
	try {
		return e();
	} finally {
		dt();
	}
}
var K, q = void 0;
function pt(e) {
	var t = q, n = K;
	q = void 0, K = void 0;
	try {
		return e();
	} finally {
		q = t, K = n;
	}
}
var J = void 0, Y = 0, mt = 0, ht = 0, gt = 0, _t = void 0, vt = 0;
function yt(e) {
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
function X(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
X.prototype.brand = ut, X.prototype.h = function() {
	return !0;
}, X.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? pt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, X.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && pt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, X.prototype.subscribe = function(e) {
	var t = this;
	return Ot(function() {
		var n = t.value;
		pt(function() {
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
	return pt(function() {
		return e.value;
	});
}, Object.defineProperty(X.prototype, "value", {
	get: function() {
		var e = yt(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (mt > 100) throw Error("Cycle detected");
			(function(e) {
				Y !== 0 && mt === 0 && e.l !== gt && (e.l = gt, _t = {
					S: e,
					v: e.v,
					i: e.i,
					o: _t
				});
			})(this), this.v = e, this.i++, vt++, Y++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				dt();
			}
		}
	}
});
function bt(e, t) {
	return new X(e, t);
}
function xt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function St(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Ct(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function Z(e, t) {
	X.call(this, void 0, t), this.x = e, this.s = void 0, this.g = vt - 1, this.f = 4;
}
Z.prototype = new X(), Z.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === vt)) return !0;
	if (this.g = vt, this.f |= 1, this.i > 0 && !xt(this)) return this.f &= -2, !0;
	var e = q;
	try {
		St(this), q = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return q = e, Ct(this), this.f &= -2, !0;
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
	var e = yt(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function wt(e, t) {
	return new Z(e, t);
}
function Tt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		Y++;
		var n = q;
		q = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, Et(e), t;
		} finally {
			q = n, dt();
		}
	}
}
function Et(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Tt(e);
}
function Dt(e) {
	if (q !== this) throw Error("Out-of-order effect");
	Ct(this), q = e, this.f &= -2, 8 & this.f && Et(this), dt();
}
function Q(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, K && K.push(this);
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
	this.f |= 1, this.f &= -9, Tt(this), St(this), Y++;
	var e = q;
	return q = this, Dt.bind(this, e);
}, Q.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = J, J = this);
}, Q.prototype.d = function() {
	this.f |= 8, 1 & this.f || Et(this);
}, Q.prototype.dispose = function() {
	this.d();
};
function Ot(e, t) {
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
var kt, At, jt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Mt = [];
Ot(function() {
	kt = this.N;
})();
function $(e, t) {
	m[e] = t.bind(null, m[e] || function() {});
}
function Nt(e) {
	if (At) {
		var t = At;
		At = void 0, t();
	}
	At = e && e.S();
}
function Pt(e) {
	var t = this, n = e.data, r = It(n);
	r.name = "ReactiveDom", r.value = n;
	var i = ze(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = wt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = wt(function() {
			return !Array.isArray(i.value) && !g(i.value);
		}), o = Ot(function() {
			if (this.N = zt, a.value) {
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
Pt.displayName = "ReactiveTextNode", Object.defineProperties(X.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Pt
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
	if (e(t), t.type !== M) {
		Nt();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return Ot(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				jt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Nt(n);
	}
}), $("__e", function(e, t, n, r) {
	Nt(), e(t, n, r);
}), $("diffed", function(e, t) {
	Nt();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Ft(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Ft(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = bt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: Ot(function() {
			this.N = zt;
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
}), N.prototype.shouldComponentUpdate = function(e, t) {
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
function It(e, t) {
	return ze(function() {
		return bt(e, t);
	}, []);
}
var Lt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Rt() {
	ft(function() {
		for (var e; e = Mt.shift();) kt.call(e);
	});
}
function zt() {
	Mt.push(this) === 1 && (m.requestAnimationFrame || Lt)(Rt);
}
//#endregion
//#region src/state/quality-goals.ts
var Bt = "/api/quality-goals?limit=200", Vt = {
	data: null,
	error: ""
}, Ht = bt(Vt), Ut = 0, Wt = wt(() => Ht.value);
wt(() => Ht.value.data?.total ?? null);
function Gt() {
	Ut += 1, Ht.value = Vt;
}
async function Kt(e) {
	let t = Ut += 1;
	try {
		let n = await I(Bt, e);
		return t === Ut && (Ht.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === Ut && (Ht.value = {
			data: null,
			error: F(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var qt = (e, t) => Kt(t), Jt = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Yt({ openItem: e, javTitleHtml: n, javDisplayName: r, srcBadge: a }) {
	let { data: o, error: s } = Wt.value;
	if (s) return /* @__PURE__ */ W("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: i(s, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let c = o?.items ?? [];
	return c.length ? /* @__PURE__ */ W("div", {
		class: "qualitylist",
		children: c.map((t) => /* @__PURE__ */ W("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ W("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${r(t)}`,
				onClick: () => e(t.id),
				children: /* @__PURE__ */ W("img", {
					src: Jt(t),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ W("div", { children: [
				/* @__PURE__ */ W("h3", { children: /* @__PURE__ */ W("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(t.id),
					dangerouslySetInnerHTML: { __html: n(t) }
				}) }),
				/* @__PURE__ */ W("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ W("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: a(t.location, t.cost) }
						}),
						/* @__PURE__ */ W("span", { children: u[t.location] ?? t.location }),
						/* @__PURE__ */ W("span", { children: d(t.duration) }),
						/* @__PURE__ */ W("span", { children: f(t.size ?? 0) })
					]
				}),
				t.reason ? /* @__PURE__ */ W("p", { children: t.reason }) : null
			] })]
		}, t.id))
	}) : /* @__PURE__ */ W("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: t("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/islands/scraping.tsx
var Xt = (e, t) => I("/api/scraping", t);
function Zt({ value: e, onChange: t }) {
	let n = U(null), r = U(t);
	return r.current = t, H(() => {
		let t = n.current;
		t.innerHTML = o([
			["environment", "系统代理"],
			["direct", "应用直连"],
			["proxy", "自定义代理"]
		], e, { label: "连接方式" });
		let i = l(t.firstElementChild), a = () => r.current(i.value);
		return i.addEventListener("change", a), () => {
			i.disabled = !0, i.removeEventListener("change", a), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ W("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Qt({ source: e, toast: t }) {
	let [r, a] = V(e), [o, s] = V(e.network), [l, u] = V(""), [d, f] = V(""), [p, m] = V(""), [h, g] = V("paste"), [_, v] = V(""), [y, b] = V(!1), [x, S] = V(""), [C, w] = V([]), T = U(null), E = U(null);
	H(() => {
		E.current?.querySelectorAll("footer button").forEach((e) => c(e, y));
	}, [y]);
	let D = U(new AbortController());
	Re(() => () => D.current.abort(), []);
	async function O(n) {
		if (!y) {
			b(!0), S(""), w([]);
			try {
				if (n === "check") {
					let t = await L("/api/scraping/check", { source: e.source }, "POST", D.current.signal);
					D.current.signal.aborted || w(t.results);
				} else {
					let r = await L("/api/scraping/settings", {
						source: e.source,
						network: o,
						proxy: l,
						cookie: d,
						cookies_text: p,
						revoke: n === "revoke"
					}, "POST", D.current.signal);
					D.current.signal.aborted || (a(r.saved), u(""), f(""), m(""), v(""), T.current && (T.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				D.current.signal.aborted || S(F(e));
			} finally {
				D.current.signal.aborted || b(!1);
			}
		}
	}
	return /* @__PURE__ */ W("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ W("form", {
			ref: E,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), O("save");
			},
			children: [/* @__PURE__ */ W("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ W("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: e.login
					}),
					/* @__PURE__ */ W("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ W(Zt, {
							value: o,
							onChange: s
						})]
					}),
					o === "proxy" && /* @__PURE__ */ W("label", { children: ["代理地址", /* @__PURE__ */ W("input", {
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: l,
						placeholder: r.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						disabled: y,
						onInput: (e) => u(e.currentTarget.value)
					})] }),
					e.accepts_cookie && /* @__PURE__ */ W(M, { children: [
						/* @__PURE__ */ W("p", { children: r.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ W("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ W("label", { children: [/* @__PURE__ */ W("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: h === t,
								onChange: () => {
									g(t), f(""), m(""), v("");
								}
							}), /* @__PURE__ */ W("span", { children: n })] }, t))
						}),
						h === "paste" ? /* @__PURE__ */ W("label", { children: ["Cookie", /* @__PURE__ */ W("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: d,
							disabled: y,
							onInput: (e) => f(e.currentTarget.value)
						})] }) : /* @__PURE__ */ W("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ W("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ W("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ W("span", {
										class: "scraping-file-name",
										children: _ || "未选择文件"
									}),
									/* @__PURE__ */ W("input", {
										ref: T,
										type: "file",
										accept: ".txt",
										disabled: y,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												m(""), v("");
												return;
											}
											if (m(""), t.size > 262144) {
												S("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											b(!0);
											try {
												let e = await t.text();
												D.current.signal.aborted || (m(e), v(t.name));
											} catch {
												D.current.signal.aborted || S("Cookie 文件未读取，请重新选择");
											} finally {
												D.current.signal.aborted || b(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					x && /* @__PURE__ */ W("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: i(x, { variant: "error" }) }
					}),
					C.map((t) => /* @__PURE__ */ W("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: i(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ W("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ W("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ W("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && r.cookie_saved && /* @__PURE__ */ W("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("revoke"),
						children: "撤销 Cookie"
					})
				]
			})]
		})
	});
}
function $t({ data: e, error: t, toast: r }) {
	let [a, o] = V(""), [s, l] = V(!1), [u, d] = V(""), f = U(null);
	H(() => c(f.current, s), [s]);
	let p = U(new AbortController()), m = U(0);
	async function h(e = !1) {
		let t = ++m.current;
		await Xe({
			read: (e) => I("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				l(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && r(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	Re(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!s) {
			m.current++, l(!0), d("");
			try {
				await L("/api/scraping/cover", { code: a }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (l(!1), d(F(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ W("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: i(t, { variant: "error" }) }
	}) : /* @__PURE__ */ W("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ W("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ W("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ W("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ W("div", { dangerouslySetInnerHTML: { __html: n("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ W("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ W("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: a,
								disabled: s,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => o(e.currentTarget.value)
							}), /* @__PURE__ */ W("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						u && /* @__PURE__ */ W("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: i(u, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ W(Qt, {
				source: e,
				toast: r
			}, e.source))
		]
	});
}
//#endregion
//#region src/state/index.ts
var en = { "quality-goals": {
	refresh: Kt,
	reset: Gt
} }, tn = () => Object.keys(en);
async function nn(e) {
	let t = en[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/native-image.ts
function rn(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function an(e, t, n, r, i = 1) {
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
function on(e, t) {
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
var sn = [
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
function cn() {
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
async function ln(e, t) {
	let n = new URLSearchParams();
	for (let t of sn) e[t] && n.set(t, e[t]);
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
function un({ kind: e = "catalog", filtered: n = !1, jav: r = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<a class=\"geist-button primary\" href=\"/configuration\">添加内容</a>" : "", s = "<a class=\"geist-button\" href=\"/follow-manage\">添加来源</a>";
	return n || r ? t("search", r ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", r ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" }) : e === "catalog" ? t("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s }) : t(e === "tags" ? "tags" : "user-round", "还没有" + ({
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
function dn(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function fn(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function pn(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function mn(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function hn(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function gn() {
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
function _n(e, t = !1, n = !1) {
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
var vn = "peach-taste-guide-dismissed";
function yn(e, t) {
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(vn, "1"), n.remove();
	});
}
//#endregion
//#region src/jav-artwork.ts
function bn(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function xn(e) {
	return {
		javLayout: bn(e.javLayout),
		javImage: Sn(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function Sn(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function Cn(e, t) {
	return e.is_jav && e.code && e.has_cover && (Sn(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function wn(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (Sn(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.removeAttribute("style"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var Tn = {
	"library-processing": {
		load: Qe,
		component: $e
	},
	scraping: {
		load: Xt,
		component: $t
	},
	"quality-goals": {
		load: qt,
		component: Yt
	},
	configuration: {
		load: rt,
		component: lt
	}
}, En = () => Object.keys(Tn), Dn = /* @__PURE__ */ new Map();
async function On(e, t, n, r = {}) {
	let i = Tn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	kn(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	Dn.set(t, a);
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
	if (Dn.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		Dn.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	Ce(ne(i.component, s), t);
}
function kn(e) {
	let t = Dn.get(e);
	t && (t.controller.abort(), Dn.delete(e), t.painted && Ce(null, e));
}
//#endregion
export { vn as TASTE_GUIDE_KEY, un as catalogEmptyHtml, ln as catalogSuggestions, gn as cleanupSkeletonHtml, mn as cloudLocations, hn as cloudPreferenceLocations, cn as emptyCatalogLayout, on as entitySkeletonHtml, Ze as followJobProgress, En as islandNames, Cn as javImageKind, rn as matchesFaceSource, On as mountIsland, an as nativeImageFit, Sn as normalizeJavImage, bn as normalizeJavLayout, xn as normalizeJavPreferences, nn as refreshStore, dn as sidebarHasCatalogContent, pn as sidebarTagCounts, tn as storeNames, wn as syncJavImages, fn as syncSidebarSurface, _n as tasteHistoryGuideHtml, kn as unmountIsland, Xe as watchJob, yn as wireTasteHistoryGuide };
