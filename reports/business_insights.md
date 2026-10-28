# Business insights

These findings describe only 50 selected products in CA_1 and CA_2, from 2015-04-26 to 2016-04-24. They are not estimates for Walmart as a whole.

## Revenue and store performance

- Calculated sales revenue: **$108,821.09** from **36,956 units**.
- Average observed sales across both stores: **101.25 units/day**.
- Highest-revenue store: **CA_1**, with **$55,900.47** (51.37% of selected revenue).
- Highest-revenue product: **FOODS_1_150**, with **$6,805.92**.

| Store_ID | Total_Units_Sold | Total_Revenue | Observed_Days | Average_Daily_Units_Sold |
| --- | --- | --- | --- | --- |
| CA_1 | 18949 | 55,900.47 | 365 | 51.92 |
| CA_2 | 18007 | 52,920.62 | 365 | 49.33 |

## ABC priorities

**26 A-class products contribute $88,515.19, or 81.34% of revenue.** Class counts are {'A': 26, 'B': 14, 'C': 10}.
Use A-class products for tighter review of replenishment parameters and more frequent cycle-count planning once real stock records are available. Revenue priority is not the same as unit velocity or profit margin.

## Fastest-moving products

Average daily sales here are product totals across BOTH stores divided by 365 days. The model's product-store daily averages are separate.

| Product_ID | Average_Daily_Units_Sold | Movement_Class | ABC_Class |
| --- | --- | --- | --- |
| FOODS_1_184 | 6.94 | Fast Moving | A |
| FOODS_3_769 | 6.37 | Fast Moving | A |
| FOODS_3_413 | 6.24 | Fast Moving | A |
| FOODS_3_070 | 6.13 | Fast Moving | C |
| FOODS_3_163 | 5.32 | Fast Moving | A |
| HOUSEHOLD_1_208 | 4.98 | Fast Moving | A |
| HOUSEHOLD_1_048 | 4.50 | Fast Moving | A |
| FOODS_3_812 | 3.99 | Fast Moving | A |
| FOODS_1_150 | 3.53 | Fast Moving | A |
| HOUSEHOLD_1_129 | 3.16 | Fast Moving | A |

## Slowest-moving products

| Product_ID | Average_Daily_Units_Sold | Movement_Class | ABC_Class |
| --- | --- | --- | --- |
| HOUSEHOLD_2_429 | 0.21 | Slow Moving | C |
| HOBBIES_1_095 | 0.22 | Slow Moving | C |
| HOUSEHOLD_2_415 | 0.33 | Slow Moving | C |
| HOUSEHOLD_1_089 | 0.37 | Slow Moving | B |
| HOBBIES_1_422 | 0.42 | Slow Moving | C |
| HOUSEHOLD_1_470 | 0.45 | Slow Moving | C |
| HOUSEHOLD_2_300 | 0.45 | Slow Moving | B |
| HOBBIES_1_245 | 0.45 | Slow Moving | B |
| HOUSEHOLD_1_163 | 0.47 | Slow Moving | A |
| HOUSEHOLD_1_472 | 0.52 | Slow Moving | B |

Slow observed sales suggest reviewing order sizes and assortment before allocating more space. They do not establish excess inventory or obsolete stock.

## Monthly demand

| Month | Units | Revenue | Days | Units_per_day |
| --- | --- | --- | --- | --- |
| 2015-04 | 407 | 1,154.25 | 5 | 81.40 |
| 2015-05 | 2975 | 7,895.01 | 31 | 95.97 |
| 2015-06 | 2947 | 7,723.44 | 30 | 98.23 |
| 2015-07 | 3287 | 8,885.40 | 31 | 106.03 |
| 2015-08 | 3381 | 9,042.54 | 31 | 109.06 |
| 2015-09 | 3138 | 8,964.06 | 30 | 104.60 |
| 2015-10 | 3075 | 9,347.00 | 31 | 99.19 |
| 2015-11 | 2713 | 9,043.39 | 30 | 90.43 |
| 2015-12 | 2778 | 9,487.87 | 31 | 89.61 |
| 2016-01 | 3041 | 9,394.33 | 31 | 98.10 |
| 2016-02 | 3055 | 9,222.40 | 29 | 105.34 |
| 2016-03 | 3228 | 9,924.50 | 31 | 104.13 |
| 2016-04 | 2931 | 8,736.90 | 24 | 122.12 |

The highest observed daily rate is **2016-04: 122.12 units/day**; the lowest is **2015-04: 81.40**.
April 2015 and April 2016 are partial months. Compare units per observed day, not their unadjusted totals. One year and a small selected basket do not prove recurring seasonality or its causes.

## Demand variability and safety stock

Highest sample standard deviations (units/day):

| Store_ID | Product_ID | Average_Daily_Demand | Demand_Standard_Deviation | Safety_Stock | Reorder_Point |
| --- | --- | --- | --- | --- | --- |
| CA_2 | FOODS_3_070 | 3.51 | 7.67 | 34 | 58 |
| CA_2 | FOODS_1_184 | 4.53 | 5.17 | 23 | 55 |
| CA_1 | FOODS_3_070 | 2.62 | 4.55 | 20 | 39 |
| CA_1 | FOODS_3_769 | 3.82 | 4.06 | 18 | 45 |
| CA_2 | FOODS_1_150 | 2.64 | 3.44 | 15 | 34 |

Products in this table have the highest estimated safety stock because the base model uses a common lead time and service factor. Review unusual demand spikes and promotional history before accepting these thresholds.

## Lead-time sensitivity

| Assumed_Lead_Time_Days | Safety_Stock | Reorder_Point |
| --- | --- | --- |
| 5 | 5.19 | 10.30 |
| 7 | 6.06 | 13.15 |
| 10 | 7.12 | 17.31 |

Figures above are averages over 100 product-store combinations. Mean lead-time demand grows linearly with lead time; the safety allowance grows with its square root. Reducing replenishment delays can lower the estimated reorder threshold, but actual lead times must be measured first.

## Practical recommendations and limits

1. Prioritize high-revenue A items for service monitoring; combine ABC and movement classes rather than treating all high-unit items as high-value items.
2. Use product-store thresholds because the stores have different demand distributions. Compare the 5/7/10-day assumptions with measured supplier delivery times before implementation.
3. Review slow items' order quantities and pack sizes. No warehouse capacity, stock on hand, order quantity, carrying cost or margin is supplied here.
4. Collect current inventory position (on hand + on order - backorders) before deciding whether to reorder. This project deliberately generates no actual reorder alerts.
5. Daily sales are observed demand proxies: zero sales could reflect zero demand, availability, or other causes. The data cannot identify actual stockouts or lost sales.
6. The normal approximation, independent daily demand and constant lead time are simplifying assumptions. A 95% target is not a measured fill rate or proven achieved service level. For intermittent demand, validate this model before use.
